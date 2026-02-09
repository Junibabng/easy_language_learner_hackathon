from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

from app.database import init_db, transaction
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatVocabExposure,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizQuestion,
    QuizResultItem,
    QuizSubmitRequest,
    QuizSubmitResponse,
    SessionResponse,
    SessionWord,
    VocabBulkRequest,
    VocabBulkResponse,
)


app = FastAPI(title="Easy Language Learner MVP", version="0.1.0")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_session(session_id: str) -> None:
    timestamp = now_iso()
    with transaction() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO sessions(id, created_at, updated_at)
            VALUES(?, ?, ?)
            """,
            (session_id, timestamp, timestamp),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )


def pull_api_key(payload_key: Optional[str], header_key: Optional[str]) -> Optional[str]:
    return payload_key or header_key


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/v1/vocab/bulk", response_model=VocabBulkResponse)
def bulk_vocab(request: VocabBulkRequest):
    ensure_session(request.session_id)
    inserted = 0
    with transaction() as conn:
        for item in request.words:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO vocab_items(session_id, target_word, translation)
                VALUES(?, ?, ?)
                """,
                (request.session_id, item.target_word.strip(), item.translation.strip()),
            )
            if cursor.rowcount == 1:
                inserted += 1
    return VocabBulkResponse(session_id=request.session_id, inserted_count=inserted)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    _api_key = pull_api_key(request.api_key, x_api_key)
    ensure_session(request.session_id)
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT target_word, translation, exposure_count, unlocked
            FROM vocab_items
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (request.session_id,),
        ).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No vocab found for session")

        exposures = []
        reply_parts = []
        for row in rows:
            next_exposure = row["exposure_count"] + 1
            unlocked = bool(row["unlocked"])
            lock = next_exposure >= 2 and not unlocked
            rendered = "[____]" if lock else row["target_word"]
            exposures.append(
                ChatVocabExposure(
                    target_word=row["target_word"],
                    rendered_word=rendered,
                    exposure_count=next_exposure,
                    lock=lock,
                    unlocked=unlocked,
                )
            )
            reply_parts.append(f"{rendered} ({row['translation']})")
            conn.execute(
                """
                UPDATE vocab_items
                SET exposure_count = ?
                WHERE session_id = ? AND target_word = ?
                """,
                (next_exposure, request.session_id, row["target_word"]),
            )

    reply = "Practice: " + ", ".join(reply_parts)
    return ChatResponse(session_id=request.session_id, reply=reply, exposures=exposures)


@app.post("/v1/quiz/generate", response_model=QuizGenerateResponse)
def quiz_generate(
    request: QuizGenerateRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    _api_key = pull_api_key(request.api_key, x_api_key)
    ensure_session(request.session_id)
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT target_word, translation
            FROM vocab_items
            WHERE session_id = ?
            ORDER BY target_word ASC
            """,
            (request.session_id,),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No vocab found for session")

    translations = [r["translation"] for r in rows]
    questions = []
    for index, row in enumerate(rows):
        correct = row["translation"]
        if len(translations) == 1:
            choices = [correct]
        else:
            distractor_one = translations[(index + 1) % len(translations)]
            distractor_two = translations[(index + 2) % len(translations)]
            choices = [correct, distractor_one]
            if distractor_two not in choices:
                choices.append(distractor_two)
        questions.append(
            QuizQuestion(
                target_word=row["target_word"],
                prompt=f"Select translation for '{row['target_word']}'",
                choices=choices,
            )
        )

    return QuizGenerateResponse(session_id=request.session_id, questions=questions)


@app.post("/v1/quiz/submit", response_model=QuizSubmitResponse)
def quiz_submit(
    request: QuizSubmitRequest,
    x_api_key: Optional[str] = Header(default=None),
):
    _api_key = pull_api_key(request.api_key, x_api_key)
    ensure_session(request.session_id)

    results = []
    with transaction() as conn:
        for answer in request.answers:
            row = conn.execute(
                """
                SELECT translation, unlocked
                FROM vocab_items
                WHERE session_id = ? AND target_word = ?
                """,
                (request.session_id, answer.target_word),
            ).fetchone()
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Word not found in session: {answer.target_word}",
                )
            correct = answer.selected_translation == row["translation"]
            unlocked = bool(row["unlocked"]) or correct
            if unlocked and not bool(row["unlocked"]):
                conn.execute(
                    """
                    UPDATE vocab_items
                    SET unlocked = 1
                    WHERE session_id = ? AND target_word = ?
                    """,
                    (request.session_id, answer.target_word),
                )
            results.append(
                QuizResultItem(
                    target_word=answer.target_word,
                    correct=correct,
                    unlocked=unlocked,
                )
            )

    return QuizSubmitResponse(session_id=request.session_id, results=results)


@app.get("/v1/session/{id}", response_model=SessionResponse)
def get_session(id: str):
    with transaction() as conn:
        session_row = conn.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (id,),
        ).fetchone()
        if session_row is None:
            raise HTTPException(status_code=404, detail="Session not found")

        rows = conn.execute(
            """
            SELECT target_word, translation, exposure_count, unlocked
            FROM vocab_items
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (id,),
        ).fetchall()

    words = [
        SessionWord(
            target_word=r["target_word"],
            translation=r["translation"],
            exposure_count=r["exposure_count"],
            unlocked=bool(r["unlocked"]),
        )
        for r in rows
    ]
    return SessionResponse(session_id=id, words=words)

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def setup_function():
    db_path = Path(__file__).resolve().parent.parent / "app.db"
    if db_path.exists():
        db_path.unlink()


def test_vocab_chat_cloze_and_unlock_flow():
    with TestClient(app) as client:
        create = client.post(
            "/v1/vocab/bulk",
            json={
                "session_id": "s1",
                "words": [
                    {"target_word": "hola", "translation": "hello"},
                    {"target_word": "adios", "translation": "goodbye"},
                ],
            },
        )
        assert create.status_code == 200
        assert create.json()["inserted_count"] == 2

        first_chat = client.post(
            "/v1/chat",
            json={"session_id": "s1", "message": "practice"},
        )
        assert first_chat.status_code == 200
        first_exposures = first_chat.json()["exposures"]
        assert all(item["lock"] is False for item in first_exposures)
        assert [item["rendered_word"] for item in first_exposures] == ["hola", "adios"]

        second_chat = client.post(
            "/v1/chat",
            json={"session_id": "s1", "message": "again"},
        )
        assert second_chat.status_code == 200
        second_exposures = second_chat.json()["exposures"]
        assert all(item["lock"] is True for item in second_exposures)
        assert [item["rendered_word"] for item in second_exposures] == ["[____]", "[____]"]

        quiz = client.post(
            "/v1/quiz/generate",
            json={"session_id": "s1"},
        )
        assert quiz.status_code == 200
        questions = quiz.json()["questions"]
        assert [q["target_word"] for q in questions] == ["adios", "hola"]

        submit = client.post(
            "/v1/quiz/submit",
            json={
                "session_id": "s1",
                "answers": [{"target_word": "hola", "selected_translation": "hello"}],
            },
        )
        assert submit.status_code == 200
        assert submit.json()["results"][0]["correct"] is True
        assert submit.json()["results"][0]["unlocked"] is True

        third_chat = client.post(
            "/v1/chat",
            json={"session_id": "s1", "message": "third"},
        )
        assert third_chat.status_code == 200
        exposures = third_chat.json()["exposures"]
        by_word = {item["target_word"]: item for item in exposures}
        assert by_word["hola"]["lock"] is False
        assert by_word["hola"]["rendered_word"] == "hola"
        assert by_word["adios"]["lock"] is True
        assert by_word["adios"]["rendered_word"] == "[____]"


def test_docs_and_session_endpoint():
    with TestClient(app) as client:
        docs = client.get("/docs")
        assert docs.status_code == 200

        client.post(
            "/v1/vocab/bulk",
            json={
                "session_id": "s2",
                "words": [{"target_word": "merci", "translation": "thanks"}],
            },
        )

        session = client.get("/v1/session/s2")
        assert session.status_code == 200
        assert session.json()["session_id"] == "s2"
        assert session.json()["words"][0]["target_word"] == "merci"


# Easy Language Learner Hackathon MVP Backend

Minimal FastAPI + SQLite backend implementing vocab exposure, cloze locking, deterministic quiz generation, and unlock-on-correct-answer flow.

## Features
- FastAPI app with OpenAPI docs at `/docs`.
- SQLite persistence via stdlib `sqlite3` (`app.db` at repo root).
- Endpoints:
  - `POST /v1/vocab/bulk`
  - `POST /v1/chat`
  - `POST /v1/quiz/generate`
  - `POST /v1/quiz/submit`
  - `GET /v1/session/{id}`
- Logic implemented:
  - First exposure in chat shows original target word.
  - Second and later exposure shows cloze `[____]` when still locked.
  - Cloze responses include `lock=true`.
  - Correct quiz answer unlocks word and subsequent chat reflects unlock.
- BYOK handling:
  - API key accepted via payload `api_key` or header `X-API-Key`.
  - Never persisted to DB/files.
  - Used only in-memory in request scope.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server: `http://127.0.0.1:8000`  
Docs: `http://127.0.0.1:8000/docs`

## Example Requests

### 1) Bulk vocab

```bash
curl -X POST http://127.0.0.1:8000/v1/vocab/bulk \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "session-1",
    "words": [
      {"target_word": "hola", "translation": "hello"},
      {"target_word": "adios", "translation": "goodbye"}
    ]
  }'
```

### 2) Chat (first exposure: original)

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: demo-key' \
  -d '{"session_id": "session-1", "message": "practice"}'
```

### 3) Chat again (second exposure: cloze + lock=true)

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "session-1", "message": "again"}'
```

### 4) Generate quiz (deterministic ordering)

```bash
curl -X POST http://127.0.0.1:8000/v1/quiz/generate \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "session-1"}'
```

### 5) Submit quiz (correct answer unlocks)

```bash
curl -X POST http://127.0.0.1:8000/v1/quiz/submit \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "session-1",
    "answers": [
      {"target_word": "hola", "selected_translation": "hello"}
    ]
  }'
```

### 6) Session state

```bash
curl http://127.0.0.1:8000/v1/session/session-1
```

## Verify

```bash
pytest -q
```


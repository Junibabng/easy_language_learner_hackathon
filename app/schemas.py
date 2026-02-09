from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VocabItem(BaseModel):
    target_word: str = Field(min_length=1)
    translation: str = Field(min_length=1)


class VocabBulkRequest(BaseModel):
    session_id: str = Field(min_length=1)
    words: List[VocabItem]


class VocabBulkResponse(BaseModel):
    session_id: str
    inserted_count: int


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    api_key: Optional[str] = None


class ChatVocabExposure(BaseModel):
    target_word: str
    rendered_word: str
    exposure_count: int
    lock: bool
    unlocked: bool


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    exposures: List[ChatVocabExposure]


class QuizGenerateRequest(BaseModel):
    session_id: str = Field(min_length=1)
    api_key: Optional[str] = None


class QuizQuestion(BaseModel):
    target_word: str
    prompt: str
    choices: List[str]


class QuizGenerateResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]


class QuizAnswer(BaseModel):
    target_word: str
    selected_translation: str


class QuizSubmitRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answers: List[QuizAnswer]
    api_key: Optional[str] = None


class QuizResultItem(BaseModel):
    target_word: str
    correct: bool
    unlocked: bool


class QuizSubmitResponse(BaseModel):
    session_id: str
    results: List[QuizResultItem]


class SessionWord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_word: str
    translation: str
    exposure_count: int
    unlocked: bool


class SessionResponse(BaseModel):
    session_id: str
    words: List[SessionWord]


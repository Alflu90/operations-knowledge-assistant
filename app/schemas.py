from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, examples=["Chi può autorizzare lo sbarco dei passeggeri?"])
    top_k: int = Field(default=3, ge=1, le=10, description="Quanti passaggi recuperare")

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value):
        return value.strip() if isinstance(value, str) else value


class Source(BaseModel):
    chunk_id: str
    source: str
    page: int
    distance: float
    text: str


class AskResponse(BaseModel):
    answer: str
    answered: bool
    latency_ms: int
    sources: list[Source]

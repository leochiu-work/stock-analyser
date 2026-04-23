from pydantic import BaseModel


class DocumentAdd(BaseModel):
    text: str
    investor: str
    source: str


class DocumentResponse(BaseModel):
    id: str
    investor: str
    source: str

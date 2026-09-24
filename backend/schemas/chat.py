from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Generado y guardado por el widget (localStorage) para que n8n pueda
    # mantener memoria de la conversación entre mensajes — ver
    # chat-widget.js, initChatSession().
    session_id: str = Field(min_length=1, max_length=100)


class ChatMessageResponse(BaseModel):
    reply: str

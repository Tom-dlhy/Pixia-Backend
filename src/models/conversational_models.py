from pydantic import BaseModel, Field
from typing import Optional, Literal

class SynthesisOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie de synthèse")
    topic: str = Field(..., description="Sujet de la conversation à générer.")
    role_agent: str = Field(..., description="Rôle de l'agent dans la conversation.")
    type : Literal["speech","textuel"] = Field("speech", description="Type de conversation qui aura lieu.")
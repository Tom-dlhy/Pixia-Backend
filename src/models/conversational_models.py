from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, List, Union, Optional, Literal

class ConversationalInit(BaseModel):
    """Permet de catégoriser la conversation qui aura lieu."""
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie de synthèse")
    topic: str = Field(..., description="Sujet de la conversation à générer.")
    role_agent: str = Field(..., description="Rôle de l'agent dans la conversation.")
    type : Literal["speech","textuel"] = Field("speech", description="Type de conversation qui aura lieu.")

class ConversationalSyntehsis(BaseModel):
    """Permet de recap la conversation qui a eu lieu dans le but de savoir si on doit faire un feedback 
    ou proposer un exo ou un cours"""
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie de synthèse")
    
    
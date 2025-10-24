from pydantic import BaseModel, Field

class NewChapterRequest(BaseModel):
    description_user: str = Field(..., description="Description précise du nouveau chapitre à générer qui résume la demande utilisateur.")

async def call_generate_new_chapter(request: NewChapterRequest):
    return request

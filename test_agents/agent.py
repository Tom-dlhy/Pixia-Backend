import asyncio
import uuid
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai.types import UserContent, Part
from pydantic import BaseModel
from typing import Optional

class Secret(BaseModel):
    id: Optional[str] = None
    secret: str

def get_secret() -> Secret:
    return Secret(id="1", secret="je suis un illuminati")

get_secret_tool = FunctionTool(func=get_secret, require_confirmation=False)

agent = LlmAgent(
    name="SecretAgent",
    instruction="Si l'utilisateur te demande un secret, appelle le tool `get_secret_tool`.",
    tools=[get_secret_tool],
)

async def test():
    runner = InMemoryRunner(agent=agent)
    content = UserContent(parts=[Part(text="Dis-moi mon secret.")])

    # ✅ créer la session via la méthode du runner (pas via session_service)
    session = await runner.create_session(
        app_name="Hackathon-App",
        user_id="user1234",
        session_id=str(uuid.uuid4()),
    )

    print("🧠 Running agent...\n")

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        print("EVENT:", event)
        if event.type == "tool_result":
            print("✅ Tool output:", event.data)

if __name__ == "__main__":
    asyncio.run(test())

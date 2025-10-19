from google import genai
from src.config import gemini_settings
from src.prompts import GENERATE_TITLE_PROMPT



async def generate_title_from_messages(messages: str) -> str | None:
    query = GENERATE_TITLE_PROMPT + messages
    answer = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=query
    )
    title= answer.text
    
    return title        




if __name__ == "__main__":
    import asyncio

    async def main():
        sample_messages = """
        
        Résume moi la vie de ce gros alien d'elon musk
        
        """
        title = await generate_title_from_messages(sample_messages)
        print("Generated Title:", title)

    asyncio.run(main())

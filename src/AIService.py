from openai import AsyncOpenAI
from qasync import asyncSlot
from PySide6.QtCore import QObject, Signal

GEMINI_API_KEY = ""
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_NAME = "gemini-2.5-flash" 

class LLMService(QObject):

    aiCompleted = Signal(str, str)
    def __init__(self):
        super().__init__()
        self.client = AsyncOpenAI(
            api_key=GEMINI_API_KEY, 
            base_url=GEMINI_BASE_URL
        )
        self.model = MODEL_NAME
    
    @asyncSlot(str, str)
    async def send_text_prompt(self, prompt, text):
        print(f"Sending text prompt: {prompt}, input: {text}")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}]
        )

        res = response.choices[0].message.content
        print(f"AI Response: {res}")

        self.aiCompleted.emit(prompt, res)
    
    @asyncSlot(str, str)
    async def send_image_prompt(self, prompt, image_data: str):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        },
                    },
                ],
            }
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        res = response.choices[0].message.content
        print(f"AI Image Response: {res}")
        self.aiCompleted.emit(prompt, res)
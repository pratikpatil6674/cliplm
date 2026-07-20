from openai import AsyncOpenAI
from qasync import asyncSlot
from PySide6.QtCore import QObject, Signal

class LLMService(QObject):
    aiCompleted = Signal(str, str)

    def __init__(self, endpoint=None, api_key=None, model=None):
        super().__init__()
        self.client = None
        self.model = model
        self.configure(endpoint=endpoint, api_key=api_key, model=model)

    def configure(self, endpoint=None, api_key=None, model=None):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=endpoint,
        )

    async def complete_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    
    @asyncSlot(str, str)
    async def send_text_prompt(self, prompt, text):
        # print(f"Sending text prompt: {prompt}, input: {text}")
        res = await self.complete_text(f"{prompt}\n\n{text}")

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
        self.aiCompleted.emit(prompt, res)

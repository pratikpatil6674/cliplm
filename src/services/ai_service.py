from openai import AsyncOpenAI
from qasync import asyncSlot
from PySide6.QtCore import QObject, Signal


class LLMService(QObject):
    aiChunk = Signal(int, str)
    aiCompleted = Signal(int, str)
    aiFailed = Signal(int, str)

    def __init__(
        self,
        endpoint=None,
        api_key=None,
        model=None,
        profile_name=None,
    ):
        super().__init__()
        self.client = None
        self.model = model
        self.profile_name = profile_name
        self.configure(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            profile_name=profile_name,
        )

    def configure(
        self,
        endpoint=None,
        api_key=None,
        model=None,
        profile_name=None,
    ):
        self.model = model
        self.profile_name = profile_name
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

    async def _stream_ai_prompt(self, request_id, messages):
        # Snapshot settings so profile changes do not alter an in-flight request.
        client, model = self.client, self.model
        parts = []
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async with stream:
            async for chunk in stream:
                for choice in chunk.choices:
                    if choice.index != 0:
                        continue
                    delta = choice.delta.content or ""
                    if delta:
                        parts.append(delta)
                        self.aiChunk.emit(request_id, delta)
        return "".join(parts)

    @asyncSlot(str, str, int)
    async def send_text_prompt(self, prompt, text, request_id):
        try:
            result = await self._stream_ai_prompt(
                request_id,
                [{"role": "user", "content": f"{prompt}\n\n{text}"}],
            )
            self.aiCompleted.emit(request_id, result)
        except Exception as error:
            self.aiFailed.emit(request_id, str(error))

    @asyncSlot(str, str, int)
    async def send_image_prompt(self, prompt, image_data: str, request_id):
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

        try:
            result = await self._stream_ai_prompt(request_id, messages)
            self.aiCompleted.emit(request_id, result)
        except Exception as error:
            self.aiFailed.emit(request_id, str(error))

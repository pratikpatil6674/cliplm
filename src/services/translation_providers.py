"""Interchangeable translation provider strategies."""

from __future__ import annotations

from typing import Protocol

from googletrans import LANGUAGES, Translator


class TranslationProvider(Protocol):
    """Contract implemented by every translation backend."""

    async def translate(self, text: str, source: str, destination: str) -> str:
        ...


class GoogleTranslationProvider:
    """Adapt googletrans to the provider-independent translation contract."""

    async def translate(self, text: str, source: str, destination: str) -> str:
        async with Translator() as translator:
            result = await translator.translate(text, src=source, dest=destination)
            return result.text


class LLMTranslationProvider:
    """Translate through the currently configured OpenAI-compatible service."""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    async def translate(self, text: str, source: str, destination: str) -> str:
        service = self.llm_service
        if service is None or service.client is None or not service.model:
            return (
                "LLM API is not configured. Select a default LLM profile "
                "in Settings."
            )

        source_label = self._language_label(source, allow_auto=True)
        destination_label = self._language_label(destination)
        prompt = (
            f"Translate the following text from {source_label} to "
            f"{destination_label}.\n"
            "Return only the translated text. Do not add explanation, notes, "
            "or quotes.\n\n"
            f"{text}"
        )
        return await service.complete_text(prompt)

    @staticmethod
    def _language_label(code: str, allow_auto: bool = False) -> str:
        if allow_auto and code == "auto":
            return "the automatically detected source language"
        return LANGUAGES.get(code, code).title()

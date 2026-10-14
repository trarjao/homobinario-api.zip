"""Camada de acesso ao Gemini.

Única porta de saída da arquitetura para o modelo. Nenhum componente fala com o
provedor diretamente: o Schedule e os handlers solicitam geração por aqui.
"""

from __future__ import annotations

import json
import re
from typing import Any

from google import genai
from google.genai import types

from .config import settings


class GeminiError(RuntimeError):
    """Falha na comunicação com o modelo."""


def extract_json(text: str) -> dict[str, Any]:
    """Isola o primeiro objeto JSON de uma resposta do modelo."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise GeminiError("A resposta do modelo não contém um objeto JSON.")

    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GeminiError(f"JSON inválido na resposta do modelo: {exc}") from exc


class GeminiClient:
    """Cliente do modelo, com a chave resolvida em tempo de construção."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key if api_key is not None else settings.gemini_api_key).strip()
        self.model = model or settings.gemini_model
        self._client = genai.Client(api_key=self.api_key) if self.api_key else None

    @property
    def available(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------ interno
    def _call(self, contents: str, config: types.GenerateContentConfig) -> str:
        if self._client is None:
            raise GeminiError("GEMINI_API_KEY ausente. Defina a chave no arquivo .env.")
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 — normalizado em GeminiError
            raise GeminiError(f"Falha na chamada ao modelo: {exc}") from exc

        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise GeminiError("O modelo retornou uma resposta vazia.")
        return text

    # ------------------------------------------------------------------ público
    def generate(
        self,
        contents: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            temperature=settings.temperature if temperature is None else temperature,
            max_output_tokens=max_output_tokens,
        )
        return self._call(contents, config)

    def generate_json(
        self,
        contents: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            temperature=settings.temperature if temperature is None else temperature,
            response_mime_type="application/json",
        )
        return extract_json(self._call(contents, config))
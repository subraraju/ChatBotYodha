"""
Unified LLM service — dispatches to OpenAI or Ollama based on config.

Usage:
    from app.services.llm_service import llm_service
    response = await llm_service.chat("Hello!", conversation_history=[...])
"""

import logging
from typing import List, Dict, Optional

import httpx
from openai import AsyncOpenAI, RateLimitError, APIError

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    f"You are {settings.COMPANY_NAME}'s customer-support assistant. "
    "Be concise, friendly, and helpful. When the customer asks about a product "
    "they purchased, provide relevant details. When they need to schedule a "
    "meeting, guide them clearly."
)


# ── Service class ─────────────────────────────────────────────────────

class LLMService:
    """Thin wrapper around OpenAI / Ollama HTTP APIs."""

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER  # "openai" or "ollama"
        self._openai: Optional[AsyncOpenAI] = None

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # ── public --------------------------------------------------------

    async def chat(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Return an assistant reply. Falls back across providers."""
        sys = system_prompt or _SYSTEM_PROMPT
        history = conversation_history or []

        if self.provider == "openai" and self._openai:
            return await self._call_openai(sys, prompt, history, max_tokens)

        if self.provider == "ollama":
            return await self._call_ollama(sys, prompt, history, max_tokens)

        # Fallback — try ollama, then openai
        try:
            return await self._call_ollama(sys, prompt, history, max_tokens)
        except Exception:
            if self._openai:
                return await self._call_openai(sys, prompt, history, max_tokens)
            raise RuntimeError("No LLM provider available")

    # ── OpenAI --------------------------------------------------------

    async def _call_openai(
        self, system: str, prompt: str, history: List[Dict], max_tokens: int
    ) -> str:
        messages = [{"role": "system", "content": system}]
        for m in history[-20:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        logger.debug("OpenAI request: model=%s tokens=%d", settings.OPENAI_MODEL, max_tokens)
        try:
            resp = await self._openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except RateLimitError as exc:
            logger.error("OpenAI quota/rate-limit error: %s", exc)
            raise RuntimeError(
                "I'm currently unable to process your request due to API limits. "
                "Please try again in a moment or contact support."
            ) from exc
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise RuntimeError(
                "I encountered an issue reaching the AI service. Please try again shortly."
            ) from exc

    # ── Ollama --------------------------------------------------------

    async def _call_ollama(
        self, system: str, prompt: str, history: List[Dict], max_tokens: int
    ) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        messages = [{"role": "system", "content": system}]
        for m in history[-20:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})

        model = settings.OLLAMA_CHAT_MODEL
        logger.debug("Ollama request: model=%s url=%s", model, url)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                url,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()


# ── Singleton ─────────────────────────────────────────────────────────

llm_service = LLMService()

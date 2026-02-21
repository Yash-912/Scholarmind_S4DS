"""
LLM Gateway — Unified interface to multiple LLM providers.
Routes queries to the cheapest capable provider (Groq primary, HF fallback).
Tracks usage and costs.
"""

import time
from groq import AsyncGroq
from typing import AsyncIterator
from app.config import settings


# Cost per 1M tokens (approximate)
MODEL_COSTS = {
    # Groq models (fast + cheap)
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "gemma2-9b-it": {"input": 0.20, "output": 0.20},
}


class LLMGateway:
    """
    Unified LLM gateway with model routing, cost tracking,
    and provider failover.
    """

    def __init__(self):
        self.groq_client = None
        self._initialized = False
        self._total_cost = 0.0
        self._total_requests = 0

    def initialize(self):
        """Initialize LLM clients."""
        if self._initialized:
            return

        if settings.GROQ_API_KEY:
            self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            print("✅ Groq client initialized")
        else:
            print("⚠️ No GROQ_API_KEY set — LLM queries will fail")

        self._initialized = True

    async def generate(
        self,
        prompt: str,
        model: str = None,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """
        Generate text from an LLM.

        Args:
            prompt: User prompt
            model: Model ID (default: settings.DEFAULT_SYNTHESIS_MODEL)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max output tokens
            stream: Whether to stream the response

        Returns:
            dict with: text, model, input_tokens, output_tokens, cost_usd, latency_ms
        """
        if not self._initialized:
            self.initialize()

        model = model or settings.DEFAULT_SYNTHESIS_MODEL

        start = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # Calculate cost
            cost_rates = MODEL_COSTS.get(model, {"input": 0.5, "output": 0.5})
            cost = (input_tokens / 1_000_000) * cost_rates["input"] + (
                output_tokens / 1_000_000
            ) * cost_rates["output"]

            elapsed = (time.time() - start) * 1000  # ms

            self._total_cost += cost
            self._total_requests += 1

            return {
                "text": text,
                "model": model,
                "provider": "groq",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
                "latency_ms": round(elapsed, 2),
            }

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ LLM generation failed ({model}): {e}")

            # Fallback to smaller model
            if model != "llama-3.1-8b-instant":
                print("♻️ Falling back to llama-3.1-8b-instant")
                return await self.generate(
                    prompt=prompt,
                    model="llama-3.1-8b-instant",
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream text from an LLM, yielding chunks.
        """
        if not self._initialized:
            self.initialize()

        model = model or settings.DEFAULT_SYNTHESIS_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"

    def get_stats(self) -> dict:
        """Get gateway usage statistics."""
        return {
            "total_requests": self._total_requests,
            "total_cost_usd": round(self._total_cost, 4),
            "initialized": self._initialized,
            "groq_available": self.groq_client is not None,
        }

    def get_available_models(self) -> list[dict]:
        """List available models with their costs."""
        return [
            {
                "model": model,
                "input_cost_per_1m": costs["input"],
                "output_cost_per_1m": costs["output"],
                "provider": "groq",
            }
            for model, costs in MODEL_COSTS.items()
        ]


# Global singleton
llm_gateway = LLMGateway()

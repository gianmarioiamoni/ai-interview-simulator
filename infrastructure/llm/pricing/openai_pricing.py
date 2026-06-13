# infrastructure/llm/pricing/openai_pricing.py

from dataclasses import dataclass

from infrastructure.config.settings import settings


@dataclass(frozen=True, slots=True)
class ModelPricing:
    model_name: str
    input_usd_per_million: float
    output_usd_per_million: float


# OpenAI API pricing (USD per 1M tokens) — https://openai.com/api/pricing
_MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(
        model_name="gpt-4o-mini",
        input_usd_per_million=0.15,
        output_usd_per_million=0.60,
    ),
    "gpt-4o-mini-2024-07-18": ModelPricing(
        model_name="gpt-4o-mini-2024-07-18",
        input_usd_per_million=0.15,
        output_usd_per_million=0.60,
    ),
}

_DEFAULT_MODEL = settings.chat_model


def get_model_pricing(model_name: str | None = None) -> ModelPricing:
    resolved = model_name or _DEFAULT_MODEL

    if resolved in _MODEL_PRICING:
        return _MODEL_PRICING[resolved]

    prefix = resolved.split("-2024", 1)[0]
    if prefix in _MODEL_PRICING:
        return _MODEL_PRICING[prefix]

    return _MODEL_PRICING[_DEFAULT_MODEL]


def calculate_token_cost_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    model_name: str | None = None,
) -> float:
    pricing = get_model_pricing(model_name)

    input_cost = (input_tokens / 1_000_000) * pricing.input_usd_per_million
    output_cost = (output_tokens / 1_000_000) * pricing.output_usd_per_million

    return round(input_cost + output_cost, 6)

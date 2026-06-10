# tests/infrastructure/llm/pricing/test_openai_pricing.py

from infrastructure.llm.pricing.openai_pricing import (
    calculate_token_cost_usd,
    get_model_pricing,
)


def test_get_model_pricing_for_gpt_4o_mini() -> None:
    pricing = get_model_pricing("gpt-4o-mini")

    assert pricing.model_name == "gpt-4o-mini"
    assert pricing.input_usd_per_million == 0.15
    assert pricing.output_usd_per_million == 0.60


def test_get_model_pricing_resolves_versioned_model_name() -> None:
    pricing = get_model_pricing("gpt-4o-mini-2024-07-18")

    assert pricing.input_usd_per_million == 0.15
    assert pricing.output_usd_per_million == 0.60


def test_get_model_pricing_falls_back_to_default() -> None:
    pricing = get_model_pricing("unknown-model")

    assert pricing.model_name == "gpt-4o-mini"


def test_calculate_token_cost_usd() -> None:
    # 1M input @ $0.15 + 1M output @ $0.60 = $0.75
    cost = calculate_token_cost_usd(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        model_name="gpt-4o-mini",
    )

    assert cost == 0.75

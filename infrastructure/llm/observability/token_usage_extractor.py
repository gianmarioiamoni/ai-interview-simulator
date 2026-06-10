# infrastructure/llm/observability/token_usage_extractor.py

from langchain_core.messages import AIMessage

from infrastructure.llm.contracts.llm_usage_snapshot import LLMUsageSnapshot


class TokenUsageExtractor:

    @staticmethod
    def extract(
        raw_message: AIMessage,
        model_fallback: str,
    ) -> LLMUsageSnapshot:
        usage = getattr(raw_message, "usage_metadata", None) or {}
        meta = getattr(raw_message, "response_metadata", None) or {}
        legacy = meta.get("token_usage") or {}

        input_tokens = usage.get("input_tokens") or legacy.get("prompt_tokens")
        output_tokens = usage.get("output_tokens") or legacy.get("completion_tokens")
        total_tokens = usage.get("total_tokens") or legacy.get("total_tokens")

        if total_tokens is None and input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens

        input_details = usage.get("input_token_details") or {}
        output_details = usage.get("output_token_details") or {}
        prompt_details = legacy.get("prompt_tokens_details") or {}
        completion_details = legacy.get("completion_tokens_details") or {}

        cache_read = input_details.get("cache_read")
        if cache_read is None:
            cache_read = prompt_details.get("cached_tokens")

        reasoning = output_details.get("reasoning")
        if reasoning is None:
            reasoning = completion_details.get("reasoning_tokens")

        if usage.get("total_tokens") is not None:
            source = "usage_metadata"
        elif legacy.get("total_tokens") is not None:
            source = "token_usage"
        else:
            source = "none"

        return LLMUsageSnapshot(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cache_read_tokens=cache_read,
            reasoning_tokens=reasoning,
            model_name=meta.get("model_name") or model_fallback,
            finish_reason=meta.get("finish_reason"),
            request_id=meta.get("id"),
            source=source,
        )

    @staticmethod
    def empty(model_fallback: str) -> LLMUsageSnapshot:
        return LLMUsageSnapshot(
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            cache_read_tokens=None,
            reasoning_tokens=None,
            model_name=model_fallback,
            finish_reason=None,
            request_id=None,
            source="none",
        )

# app/ui/mappers/output_mapper.py

from app.contracts.output_contract import OUTPUT_KEYS


class OutputMapper:

    @staticmethod
    def map(response_dict: dict):

        missing = set(OUTPUT_KEYS) - set(response_dict.keys())

        if missing:
            raise RuntimeError(f"Missing UI outputs: {sorted(missing)}")

        return [response_dict[key] for key in OUTPUT_KEYS]

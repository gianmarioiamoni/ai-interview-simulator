# services/question_intelligence/coverage/topic_extractor.py

TOPIC_KEYWORDS = {
    "indexing": [
        "index",
        "indexing",
    ],
    "transactions": [
        "transaction",
        "transactions",
    ],
    "sql_querying": [
        "sql",
        "join",
        "aggregation",
        "query",
    ],
    "scalability": [
        "sharding",
        "scaling",
        "distributed",
    ],
    "pooling": [
        "connection pooling",
        "pooling",
    ],
    "normalization": [
        "normalization",
    ],
}


class TopicExtractor:

    # =====================================================
    # PUBLIC
    # =====================================================

    def extract(
        self,
        text: str,
    ) -> str:

        lower = text.lower()

        for topic, keywords in TOPIC_KEYWORDS.items():

            if any(keyword in lower for keyword in keywords):
                return topic

        return "other"

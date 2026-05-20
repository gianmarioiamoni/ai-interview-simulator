# services/retrieval/planner_retrieval_service.py

from services.retrieval.contracts import (
    RetrievalPlanningIntent,
    RetrievalQuery,
)

from services.retrieval.semantic_retrieval_engine import (
    SemanticRetrievalEngine,
)

from services.retrieval.hybrid_retrieval_fusion_engine import (
    HybridRetrievalFusionEngine,
)

from services.retrieval.embedding_generator import (
    EmbeddingGenerator,
)

from services.retrieval.corpus_retrieval_preparator import (
    CorpusRetrievalPreparator,
)


class PlannerRetrievalService:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self) -> None:

        self._preparator = CorpusRetrievalPreparator()

        self._semantic_engine = SemanticRetrievalEngine()

        self._embedding_generator = EmbeddingGenerator()

        self._fusion_engine = HybridRetrievalFusionEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def retrieve_candidates(
        self,
        intent: RetrievalPlanningIntent,
        corpus_path: str,
    ):

        # -------------------------------------------------
        # LOAD CORPUS
        # -------------------------------------------------

        corpus = self._preparator.prepare(
            corpus_path=corpus_path,
        )

        # -------------------------------------------------
        # SYMBOLIC QUERY
        # -------------------------------------------------

        query = RetrievalQuery(
            text=(intent.query_text),
            required_tags=(intent.required_tags),
            preferred_categories=(intent.focus_areas),
            minimum_score=0.4,
            top_k=(intent.max_candidates),
        )

        # -------------------------------------------------
        # SYMBOLIC RETRIEVAL
        # -------------------------------------------------

        symbolic_results = self._semantic_engine.retrieve(
            query=query,
            corpus=corpus,
        )

        # -------------------------------------------------
        # EMBEDDINGS
        # -------------------------------------------------

        embedding_records = self._embedding_generator.generate(corpus)

        # -------------------------------------------------
        # HYBRID FUSION
        # -------------------------------------------------

        fused_results = self._fusion_engine.fuse(
            query=(intent.query_text),
            symbolic_results=(symbolic_results),
            embedding_records=(embedding_records),
        )

        return fused_results

TD-001
Semantic diversity embeddings not available at retrieval time.

TD-002
Double embedding generation in corpus build pipeline.

TD-003
Duplicate RetrievalDocument contracts.

TD-004
Legacy services/retrieval still owns orchestrator path.

TD-005

Extract TargetAreaResolver

services/question_corpus/resolvers/target_area_resolver.py

TD-006
Un piccolo problema che vedo

Nel mapper:

domains=[area.value]

Questa è una soluzione temporanea accettabile per la Phase 4A.

Ma va considerata debito tecnico.

Per esempio:

technical_database

non è un domain.

È un'area.

Mentre:

sql
transactions
indexing
query_optimization

sono domains.

Per ora va bene.

Ma metterei già un TODO.
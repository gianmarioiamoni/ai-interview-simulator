TD-001
Semantic diversity embeddings not available at retrieval time.

TD-002
Double embedding generation in corpus build pipeline.

TD-003
~~Duplicate RetrievalDocument contracts.~~ Closed in Phase 8E-B: orphan domain retrieval stack removed; canonical runtime contract is `services/question_corpus/contracts/retrieval_document.py`.

TD-004
~~Legacy services/retrieval still owns orchestrator path.~~ Closed in Phase 8D-A3: legacy engine excised; production uses domain contracts + question_corpus runtime.

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


TD-007
Osservazione sul filtro "_ACTIONABLE_SQL_PATTERN"

Qui farei attenzione.

Attualmente:

_ACTIONABLE_SQL_PATTERN

cerca parole come:

write
query
select
join
aggregate
count
group by
where

Funziona.

Però rischia di escludere parecchie domande database utili.

Esempio:

What is the difference between a primary key and a unique index?

verrebbe scartata.

Mentre un LLM potrebbe tranquillamente trasformarla in:

Using the employees table...
write a query...

Quindi io la considererei una soluzione temporanea.


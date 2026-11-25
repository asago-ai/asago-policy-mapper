"""Lock-free numbering for pipeline-stage LLM call records.

Call ids (``judge-001``, ``ground-002``, …) number the records a run
collects, per id format. Numbering happens in two steps with no shared
mutable state between worker threads:

1. A stage worker numbers the records it builds against its own records
   list (``next_call_number``). Each list has exactly one writer — the
   worker — so the count needs no lock.
2. The stage coordinator merges each task's list into the run's collector
   at fan-in (``merge_call_records``), on the main thread, renumbering by
   the same counting predicate. Merged ids therefore follow task order,
   not completion order: a run's ids are deterministic however the
   workers interleaved.

Each record site keeps its own counting predicate (matching its id
format); records with no predicate, such as query generation's
``querygen-<chunk>`` ids, merge as built.
"""

from __future__ import annotations

from collections.abc import Callable

from asago_policy_mapper.extract.models import LLMCallRecord


def next_call_number(records: list[LLMCallRecord], *, counts: Callable[[LLMCallRecord], bool]) -> int:
    """Return one past the number of matching records in ``records``.

    ``counts`` selects which records the numbering considers, so each call
    site keeps its legacy predicate and id format. Safe only while one
    thread owns ``records``; fan-in merges do the cross-task numbering.
    """
    return sum(1 for record in records if counts(record)) + 1


def merge_call_records(
    collector: list[LLMCallRecord],
    records: list[LLMCallRecord],
    *,
    counts: Callable[[LLMCallRecord], bool] | None = None,
) -> None:
    """Append a task's records to the run's collector, renumbering if needed.

    With ``counts`` (a numbered id format), each appended record that matches
    the predicate takes the next number past the collector's matching
    records, rewriting ``call_id`` in place as ``<prefix>-<n>`` — the prefix
    is the record's id up to its last dash. Ids stay unique across tasks and
    follow task order. Records that do not match keep their ids. Without
    ``counts`` the records keep the call ids they were built with.
    """
    if counts is None:
        collector.extend(records)
        return
    for record in records:
        if counts(record):
            number = next_call_number(collector, counts=counts)
            record.call_id = f"{record.call_id.rsplit('-', 1)[0]}-{number:03d}"
        collector.append(record)

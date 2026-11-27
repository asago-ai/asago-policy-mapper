"""Extraction package: run_extraction and its result/config models.

The pipeline imports lazily: ``extract`` submodules (``screening``,
``retrieve``) are imported by the assessors package first, and an eager
``pipeline`` import here would make that circular
(``assessors.llm_judge`` -> ``extract.screening`` -> ``extract/__init__``
-> ``extract.pipeline`` -> ``extract.retrieve`` -> ``assessors.llm_judge``).
``tests/test_extract_screening.py::test_assessors_import_without_extract_pipeline``
pins that import order: an eager submodule import added here fails it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asago_policy_mapper.extract.models import ExtractionResult, RetrievalConfig
    from asago_policy_mapper.extract.pipeline import run_extraction

__all__ = ["ExtractionResult", "RetrievalConfig", "run_extraction"]


def __getattr__(name: str):
    if name == "ExtractionResult":
        from asago_policy_mapper.extract.models import ExtractionResult

        return ExtractionResult
    if name == "RetrievalConfig":
        from asago_policy_mapper.extract.models import RetrievalConfig

        return RetrievalConfig
    if name == "run_extraction":
        from asago_policy_mapper.extract.pipeline import run_extraction

        return run_extraction
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

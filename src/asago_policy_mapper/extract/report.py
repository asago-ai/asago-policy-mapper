import base64
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from asago_policy_mapper.extract.report_themes import enrich_report_themes

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


@lru_cache(maxsize=1)
def _report_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "jinja2")),
        undefined=StrictUndefined,
    )
    # Keep support for values such as datetimes in saved results when embedding JSON.
    environment.policies["json.dumps_kwargs"] = {"default": str, "sort_keys": False}
    return environment


def build_risk_extraction_report(data: dict, output_path: Path) -> Path:
    logo = base64.b64encode((TEMPLATE_DIR / "assets" / "asago-main-logo-dark.svg").read_bytes()).decode("ascii")
    html = (
        _report_environment()
        .get_template("risk_extraction_report.jinja2")
        .render(
            report_data=enrich_report_themes(data),
            logo_src=f"data:image/svg+xml;base64,{logo}",
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    return output_path


def build_annotation_report(data: dict, output_path: Path) -> Path:
    html = _report_environment().get_template("annotation_report.jinja2").render(report_data=data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    return output_path

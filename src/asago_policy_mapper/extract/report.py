import base64
import re
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from asago_policy_mapper.extract.report_themes import enrich_report_themes

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
VENDOR_DIR = TEMPLATE_DIR / "vendor"


@lru_cache(maxsize=1)
def _browser_assets() -> tuple[str, str, str]:
    patternfly_dir = VENDOR_DIR / "patternfly-6.6.1"
    css = (patternfly_dir / "patternfly.min.css").read_text()

    def inline_asset(match: re.Match[str]) -> str:
        asset_name = match.group(1).strip("\"'").removeprefix("./")
        asset = patternfly_dir / asset_name
        mime_type = "font/woff2" if asset.suffix == ".woff2" else "image/svg+xml"
        encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
        return f'url("data:{mime_type};base64,{encoded}")'

    css = re.sub(r"url\(([^)]+)\)", inline_asset, css)
    css = css.replace("/*# sourceMappingURL=patternfly.min.css.map */", "")
    css += "\n" + (patternfly_dir / "patternfly-addons.css").read_text()
    alpine_dir = VENDOR_DIR / "alpine-3.17.4"
    alpine = (alpine_dir / "cdn.min.js").read_text()
    license_files = (
        patternfly_dir / "LICENSE.txt",
        alpine_dir / "LICENSE.md",
        patternfly_dir / "REDHAT-FONT-OFL.txt",
        patternfly_dir / "FONT-AWESOME-LICENSE.txt",
    )
    notices = "\n\n".join(f"{path.name}\n{path.read_text()}" for path in license_files)
    return css, alpine, notices


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
    patternfly_css, alpine_js, vendor_notices = _browser_assets()
    html = (
        _report_environment()
        .get_template("risk_extraction_report.jinja2")
        .render(
            report_data=enrich_report_themes(data),
            logo_src=f"data:image/svg+xml;base64,{logo}",
            patternfly_css=patternfly_css,
            alpine_js=alpine_js,
            vendor_notices=vendor_notices,
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

"""Download official National Health Profile workbooks via the public guest UI.

No private endpoint guessing or credential injection: automate the same
Kommune -> Export Data workflow documented by the publisher.
Optional dependency: pip install -r requirements-health.txt; playwright install chromium.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import sys
from urllib.parse import urlencode, urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
VIEWER = "https://proxy.danskernessundhed.dk/SASVisualAnalyticsViewer/VisualAnalyticsViewer_guest.jsp"
INDICATORS = {
    "daily_smoking": {"report": "Andel der ryger dagligt", "column": "Andel der ryger dagligt"},
    "obesity": {"report": "Svaer overvaegt", "column": "Andel med svær overvægt"},
    "physical_inactivity": {"report": "Opfylder ikke WHOs anbefalinger for fysisk aktivitet", "column": "Andel der ikke opfylder WHO’s minimums anbefaling for fysisk aktivitet"},
    "risky_alcohol": {"report": "Drikker mere end 10 genstande om ugen", "column": "Andel der drikker mere end 10 genstande i løbet af en typisk uge"},
    "good_self_rated_health": {"report": "Andel med godt selvvurderet helbred", "column": "Andel med fremragende, vældig godt eller godt selvvurderet helbred"},
    "poor_mental_health": {"report": "Daarligt mentalt helbred", "column": "Andel med lav score på den mentale helbredsskala"},
}


def report_url(key: str) -> str:
    return VIEWER + "?" + urlencode({"reportName": INDICATORS[key]["report"],
        "reportPath": "/Produktion/Danskernes_Sundhed/", "reportViewOnly": "true"})


def exclusive_text(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)


def export_one(page, key: str, wave: int, directory: Path) -> dict:
    """Export all municipality rows, recording UI selections and report definition."""
    url = report_url(key)
    print(f"Opening {key}, requested wave {wave} ...", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    page.get_by_role("tab", name="Kommune", exact=True).wait_for(timeout=120_000)
    page.get_by_role("tab", name="Beskrivelse af indikatoren", exact=True).click()
    rich_text = page.locator(".vavRichTextWrapper:visible")
    rich_text.first.wait_for(timeout=60_000)
    # Preserve emphasis on the response categories, not just plain text.
    definition_html = "\n".join(rich_text.evaluate_all("es=>es.map(e=>e.outerHTML)"))
    exclusive_text(directory / f"{key}_definition.html", definition_html)
    page.get_by_role("tab", name="Kommune", exact=True).click()
    year_item = page.get_by_text(str(wave), exact=True).first.locator("xpath=ancestor::li[1]")
    year_item.wait_for(timeout=60_000)
    year_item.click()
    page.wait_for_function("""wave => [...document.querySelectorAll('li')].some(
        e => e.innerText.trim() === String(wave) && e.querySelector('input[type=radio]:checked'))""", arg=wave)
    # No region selected means all regions, as checked against the 98-row export.
    if page.locator("input[type=checkbox]:checked").count():
        raise ValueError("Unexpected region filter; refusing a partial export")
    canvas = page.locator("canvas:visible").first
    canvas.wait_for(timeout=60_000)
    # Wait for the selected wave's data requests to settle before opening export.
    page.wait_for_load_state("networkidle", timeout=60_000)
    canvas.click(button="right", position={"x": 250, "y": 80})
    page.get_by_text("Export data...", exact=True).click()
    dialog = page.get_by_role("dialog", name="Export Data", exact=True)
    dialog.wait_for(timeout=60_000)
    row_input = page.locator("#exportDataRowsSpecifyRangeInput-inner")
    row_range = row_input.get_attribute("placeholder")
    if row_range != "1-98":
        raise ValueError(f"Expected all 98 municipality rows; UI offers {row_range}")
    row_input.fill("1-98")
    if page.locator("#exportDataFormattedDataCheckBox").get_attribute("aria-checked") != "true":
        page.locator("#exportDataFormattedDataCheckBox").click()
    file_type = page.locator("#exportDataExportTypeSelect-label").inner_text()
    if file_type != "Excel workbook (*.xlsx)":
        raise ValueError(f"Unexpected default export type: {file_type}")
    columns = dialog.locator("li[role=option]").all_inner_texts()
    output = directory / f"{key}_{wave}.xlsx"
    if output.exists():
        raise FileExistsError(output)
    with page.expect_download(timeout=120_000) as download_event:
        dialog.get_by_role("button", name="OK", exact=True).click()
    download = download_event.value
    if download.failure():
        raise ValueError(f"Official export failed: {download.failure()}")
    download.save_as(output)
    result = {"indicator": key, "source_url": url, "wave": wave,
        "geography": "Kommune; all 98 municipalities", "region_filter": "none (all)",
        "population": "Report's municipality total; survey ages 16+; indicator-specific eligibility per saved definition; no subgroup selection",
        "measure": "Published prevalence; not the accompanying adjusted odds ratio",
        "rows": row_range, "formatted_data": True, "format": "xlsx",
        "export_columns": columns, "file": output.name,
        "definition_file": f"{key}_definition.html",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "definition_sha256": hashlib.sha256((directory / f"{key}_definition.html").read_bytes()).hexdigest()}
    print(f"Exported {output.name}", flush=True)
    return result


def acquire(wave: int = 2025) -> Path:
    from playwright.sync_api import sync_playwright

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / "data" / "raw" / f"health_profile_{wave}_{stamp}_{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {"source": "Den Nationale Sundhedsprofil / Danskernes Sundhed (SST and SIF/SDU)",
        "wave": wave, "status": "in_progress", "exports": [], "network_paths": [],
        "access_method": "Official public guest viewer, Kommune tab, formatted Excel export",
        "created_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 1100}, accept_downloads=True)
            # Record paths/status only: omit cookies, CAS tickets and session query parameters.
            page.on("response", lambda r: manifest["network_paths"].append({
                "path": urlsplit(r.url).path, "status": r.status})
                if r.request.resource_type in ("xhr", "fetch") and "/resources/" not in r.url else None)
            for key in INDICATORS:
                manifest["exports"].append(export_one(page, key, wave, directory))
            browser.close()
        manifest["status"] = "complete"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        exclusive_text(directory / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Raw snapshot: {directory}")
    return directory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave", type=int, choices=(2025, 2021), default=2025)
    args = parser.parse_args()
    try:
        acquire(args.wave)
    except Exception as exc:
        print(f"Health acquisition failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

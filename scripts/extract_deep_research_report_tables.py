from __future__ import annotations

import csv
import html
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

REDUNDANCY_REPORT = ROOT / "Rights-Aware Source Redundancy Audit for Modern Graphic Design History.docx"
REMEDIATION_REPORT = ROOT / "Rights-Aware Remediation of Unresolved Graphic Design Archive Targets.docx"
EXPANSION_REPORT = ROOT / "Rights-aware source expansion for a global graphic design history archive index.docx"

CELL_IDS = [f"C{index:02d}" for index in range(1, 16)]


class HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.current_cell is not None and self.current_row is not None:
            value = html.unescape("".join(self.current_cell))
            value = re.sub(r"\s+", " ", value).strip()
            self.current_row.append(value)
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = None


def docx_root(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as z:
        return ET.fromstring(z.read("word/document.xml"))


def docx_tables(path: Path) -> list[list[list[str]]]:
    root = docx_root(path)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    tables: list[list[list[str]]] = []
    for tbl in root.iter(ns + "tbl"):
        rows: list[list[str]] = []
        for tr in tbl.iter(ns + "tr"):
            cells: list[str] = []
            for tc in tr.iter(ns + "tc"):
                texts = [text.text or "" for text in tc.iter(ns + "t")]
                value = re.sub(r"\s+", " ", "".join(texts)).strip()
                cells.append(value)
            if cells:
                rows.append(cells)
        tables.append(rows)
    return tables


def docx_text(path: Path) -> str:
    root = docx_root(path)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paras: list[str] = []
    for para in root.iter(ns + "p"):
        texts = [text.text or "" for text in para.iter(ns + "t")]
        value = "".join(texts).strip()
        if value:
            paras.append(value)
    return "\n".join(paras)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


def clean_label(value: str) -> str:
    return re.sub(r"\s*\[\d+\]\s*$", "", value).strip()


def extract_redundancy() -> None:
    tables = docx_tables(REDUNDANCY_REPORT)
    candidate_rows: list[dict[str, str]] = []
    for table_index, rows in enumerate(tables[:15]):
        cell_id = CELL_IDS[table_index]
        header = rows[0]
        for row_index, raw_row in enumerate(rows[1:], start=1):
            row = dict(zip(header, raw_row))
            candidate_rows.append(
                {
                    "redundancy_candidate_id": f"SRCAND{table_index + 1:02d}{row_index:02d}",
                    "scope_cell_id": cell_id,
                    "candidate_label": clean_label(row.get("Candidate", "")),
                    "candidate_class": row.get("Class", ""),
                    "creator_or_institution": row.get("Creator / institution", ""),
                    "date_text": row.get("Date", ""),
                    "source_name": row.get("Source", ""),
                    "url_or_search_path": row.get("URL or search path", ""),
                    "record_family": row.get("Family", ""),
                    "expected_image_zone": row.get("Img", ""),
                    "rights_risk": row.get("Rights", ""),
                    "automation_feasibility": row.get("Auto", ""),
                    "replace_failed_target": row.get("Replace failed target", ""),
                }
            )

    write_csv(
        DATA / "source_redundancy_candidates.csv",
        [
            "redundancy_candidate_id",
            "scope_cell_id",
            "candidate_label",
            "candidate_class",
            "creator_or_institution",
            "date_text",
            "source_name",
            "url_or_search_path",
            "record_family",
            "expected_image_zone",
            "rights_risk",
            "automation_feasibility",
            "replace_failed_target",
        ],
        candidate_rows,
    )

    triage_rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(tables[15][1:], start=1):
        triage_rows.append(
            {
                "triage_id": f"SRTRIAGE{index:03d}",
                "probable_failed_target": raw_row[0],
                "likely_failure_mode": raw_row[1],
                "recommended_action": raw_row[2],
                "best_replacement_or_next_move": raw_row[3],
            }
        )

    write_csv(
        DATA / "source_redundancy_triage.csv",
        ["triage_id", "probable_failed_target", "likely_failure_mode", "recommended_action", "best_replacement_or_next_move"],
        triage_rows,
    )

    ingest_set_rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(tables[16][1:], start=1):
        ingest_set_rows.append(
            {
                "recommended_set_id": f"SRSET{index:03d}",
                "scope_cell_id": raw_row[0],
                "recommended_six_target_ingest_set": raw_row[1],
            }
        )

    write_csv(
        DATA / "recommended_six_target_ingest_sets.csv",
        ["recommended_set_id", "scope_cell_id", "recommended_six_target_ingest_set"],
        ingest_set_rows,
    )


def extract_remediation() -> None:
    text = docx_text(REMEDIATION_REPORT)
    match = re.search(r"<table>.*?</table>", text, flags=re.DOTALL)
    if not match:
        raise SystemExit("No remediation HTML table found")
    parser = HtmlTableParser()
    parser.feed(match.group(0))
    rows = parser.rows
    header = rows[0]
    output: list[dict[str, str]] = []
    for index, raw_row in enumerate(rows[1:], start=1):
        row = dict(zip(header, raw_row))
        output.append(
            {
                "remediation_id": f"REMED{index:03d}",
                "failed_target_or_cell": row.get("failed target ID", ""),
                "original_target_label": row.get("original target label", ""),
                "original_source": row.get("original source", ""),
                "failure_type": row.get("failure type", ""),
                "confirmed_exact_url": row.get("confirmed exact URL if found", ""),
                "replacement_url": row.get("replacement URL if better", ""),
                "source_title": row.get("source title", ""),
                "creator_or_institution": row.get("creator/institution", ""),
                "date_text": row.get("date", ""),
                "record_family": row.get("record family", ""),
                "rights_note": row.get("rights note", ""),
                "recommended_image_zone": row.get("recommended IMG00-IMG04", ""),
                "recommended_status": row.get("recommended status", ""),
                "reason": row.get("reason", ""),
            }
        )

    write_csv(
        DATA / "fallback_remediation_recommendations.csv",
        [
            "remediation_id",
            "failed_target_or_cell",
            "original_target_label",
            "original_source",
            "failure_type",
            "confirmed_exact_url",
            "replacement_url",
            "source_title",
            "creator_or_institution",
            "date_text",
            "record_family",
            "rights_note",
            "recommended_image_zone",
            "recommended_status",
            "reason",
        ],
        output,
    )


def extract_expansion() -> None:
    tables = docx_tables(EXPANSION_REPORT)
    source_rows: list[dict[str, str]] = []
    for table_index, rows in enumerate(tables[1:7], start=1):
        header = rows[0]
        for row_index, raw_row in enumerate(rows[1:], start=1):
            row = dict(zip(header, raw_row))
            source_rows.append(
                {
                    "source_expansion_id": f"GSE{len(source_rows) + 1:03d}",
                    "source_name": row.get("Source", ""),
                    "region": row.get("Region", ""),
                    "source_type": row.get("Type", ""),
                    "url": row.get("URL", ""),
                    "access_method": row.get("Access method", ""),
                    "api_iiif_oai_data": row.get("API / IIIF / OAI / data", ""),
                    "likely_record_types": row.get("Likely record types", ""),
                    "graphic_design_relevance": row.get("Graphic design relevance", ""),
                    "rights_clarity": row.get("Rights clarity", ""),
                    "stable_identifier_quality": row.get("Stable ID", ""),
                    "automation_feasibility": row.get("Auto", ""),
                    "default_image_zone": row.get("IMG", ""),
                    "recommended_use": row.get("Use", ""),
                    "evidence": row.get("Evidence", ""),
                }
            )

    write_csv(
        DATA / "global_source_expansion_candidates.csv",
        [
            "source_expansion_id",
            "source_name",
            "region",
            "source_type",
            "url",
            "access_method",
            "api_iiif_oai_data",
            "likely_record_types",
            "graphic_design_relevance",
            "rights_clarity",
            "stable_identifier_quality",
            "automation_feasibility",
            "default_image_zone",
            "recommended_use",
            "evidence",
        ],
        source_rows,
    )

    low_friction_rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(tables[7][1:], start=1):
        low_friction_rows.append(
            {
                "low_friction_id": f"LF{index:03d}",
                "source_name": raw_row[0],
                "why_production_ingest": raw_row[1],
                "evidence": raw_row[2],
            }
        )

    write_csv(
        DATA / "first_production_low_friction_sources.csv",
        ["low_friction_id", "source_name", "why_production_ingest", "evidence"],
        low_friction_rows,
    )

    fragile_rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(tables[8][1:], start=1):
        fragile_rows.append(
            {
                "fragile_source_id": f"FRAG{index:03d}",
                "source_name": raw_row[0],
                "why_valuable": raw_row[1],
                "why_fragile": raw_row[2],
                "recommended_treatment": raw_row[3],
                "evidence": raw_row[4],
            }
        )

    write_csv(
        DATA / "high_value_fragile_sources.csv",
        ["fragile_source_id", "source_name", "why_valuable", "why_fragile", "recommended_treatment", "evidence"],
        fragile_rows,
    )


def main() -> None:
    extract_redundancy()
    extract_remediation()
    extract_expansion()


if __name__ == "__main__":
    main()

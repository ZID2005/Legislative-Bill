"""
reporting/formatter.py
=======================
Format-specific serialisers for StakeholderReport, BillLevelReport,
and CompanyLevelReport (Task 7.3).

Supported formats:
- JSON     : Compact JSON string representation
- MARKDOWN : Human-readable Markdown document
- CSV      : Flat summary rows (for bulk export)

Design Rules
------------
- Formatters are pure functions — no state modification.
- No prediction logic or risk computation.
- All values carried verbatim from report data structures.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Union

from config.logging_config import get_logger
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport

logger = get_logger(__name__)

# Report type union for typing
AnyReport = Union[StakeholderReport, BillLevelReport, CompanyLevelReport]

# CSV column order for StakeholderReport
_STAKEHOLDER_CSV_COLUMNS = [
    "report_id",
    "bill_id",
    "company_isin",
    "event_window",
    "stakeholder_type",
    "decision_version",
    "report_version",
    "generated_timestamp",
    "executive_summary",
]

# CSV columns for BillLevelReport
_BILL_CSV_COLUMNS = [
    "report_id",
    "bill_id",
    "bill_title",
    "bill_ministry",
    "bill_year",
    "event_window",
    "report_version",
    "generated_timestamp",
    "total_companies",
    "positive_count",
    "negative_count",
    "neutral_count",
    "market_moving_count",
    "high_impact_count",
    "avg_impact_score",
    "avg_risk_score",
    "sectors_affected",
]

# CSV columns for CompanyLevelReport
_COMPANY_CSV_COLUMNS = [
    "report_id",
    "company_isin",
    "company_name",
    "company_sector",
    "report_version",
    "generated_timestamp",
    "total_bills",
    "positive_bill_count",
    "negative_bill_count",
    "neutral_bill_count",
    "avg_impact_score",
    "avg_risk_score",
    "high_impact_bills",
]


class ReportFormatter:
    """
    Converts report objects to JSON, Markdown, or CSV string representations.
    All methods are stateless and raise no side-effects.
    """

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def to_json(self, report: AnyReport, indent: int = 2) -> str:
        """
        Serialise a report to a formatted JSON string.

        Parameters
        ----------
        report : StakeholderReport | BillLevelReport | CompanyLevelReport
        indent : int

        Returns
        -------
        str
        """
        return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False, default=str)

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def to_markdown(self, report: AnyReport) -> str:
        """
        Serialise a report to a Markdown-formatted string.
        """
        if isinstance(report, StakeholderReport):
            return self._stakeholder_to_markdown(report)
        elif isinstance(report, BillLevelReport):
            return self._bill_to_markdown(report)
        elif isinstance(report, CompanyLevelReport):
            return self._company_to_markdown(report)
        else:
            logger.warning("Unknown report type for Markdown formatting: %s", type(report))
            return json.dumps(report.to_dict(), indent=2, default=str)

    def _stakeholder_to_markdown(self, r: StakeholderReport) -> str:
        """Format a StakeholderReport as Markdown."""
        stakeholder = r.stakeholder_type.title()
        lines = [
            f"# Legislative Market Impact Report — {stakeholder} View",
            "",
            f"**Report ID**: `{r.report_id}`  ",
            f"**Bill ID**: `{r.bill_id}`  ",
            f"**Company ISIN**: `{r.company_isin}`  ",
            f"**Event Window**: `{r.event_window}`  ",
            f"**Stakeholder Type**: {stakeholder}  ",
            f"**Report Version**: {r.report_version}  ",
            f"**Generated**: {r.generated_timestamp}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            r.executive_summary,
            "",
            "---",
            "",
            "## Bill Overview",
            "",
            "```",
            r.bill_summary,
            "```",
            "",
            "## Company Overview",
            "",
            "```",
            r.company_summary,
            "```",
            "",
            "## Market Impact Analysis",
            "",
            "```",
            r.impact_summary,
            "```",
            "",
            "## Risk Assessment",
            "",
            "```",
            r.risk_summary,
            "```",
            "",
            "## Pre-Event Anticipation",
            "",
            "```",
            r.anticipation_summary,
            "```",
            "",
            "## Model Confidence",
            "",
            "```",
            r.confidence_summary,
            "```",
            "",
        ]

        if r.key_factors:
            lines += [
                "## Key Factors",
                "",
            ]
            for factor in r.key_factors:
                lines.append(f"- {factor}")
            lines.append("")

        if r.methodology_note:
            lines += [
                "---",
                "",
                "## Methodology Note",
                "",
                f"*{r.methodology_note}*",
                "",
            ]

        if r.disclaimer:
            lines += [
                "---",
                "",
                "## Disclaimer",
                "",
                f"> **{r.disclaimer}**",
                "",
            ]

        return "\n".join(lines)

    def _bill_to_markdown(self, r: BillLevelReport) -> str:
        """Format a BillLevelReport as Markdown."""
        lines = [
            f"# Bill-Level Market Impact Summary",
            "",
            f"**Report ID**: `{r.report_id}`  ",
            f"**Bill ID**: `{r.bill_id}`  ",
            f"**Bill Title**: {r.bill_title}  ",
            f"**Ministry**: {r.bill_ministry or 'N/A'}  ",
            f"**Year**: {r.bill_year or 'N/A'}  ",
            f"**Event Window**: `{r.event_window}`  ",
            f"**Report Version**: {r.report_version}  ",
            f"**Generated**: {r.generated_timestamp}",
            "",
            "---",
            "",
            "## Aggregate Statistics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Companies Affected | {r.total_companies} |",
            f"| Positive Impact Predictions | {r.positive_count} |",
            f"| Negative Impact Predictions | {r.negative_count} |",
            f"| Neutral Impact Predictions | {r.neutral_count} |",
            f"| Market-Moving Predictions (≥50%) | {r.market_moving_count} |",
            f"| High/Very-High Impact Predictions | {r.high_impact_count} |",
            f"| Average Impact Score | {r.avg_impact_score:.4f} |",
            f"| Average Risk Score | {r.avg_risk_score:.4f} |",
            "",
            "## Sectors Potentially Affected",
            "",
        ]
        if r.sectors_affected:
            for s in r.sectors_affected:
                lines.append(f"- {s}")
        else:
            lines.append("*No sector data available.*")
        lines.append("")

        # Anticipation distribution
        if r.anticipation_distribution:
            lines += [
                "## Anticipation Distribution",
                "",
                "| Classification | Count |",
                "|----------------|-------|",
            ]
            for cls, cnt in sorted(r.anticipation_distribution.items()):
                lines.append(f"| {cls.replace('_', ' ').title()} | {cnt} |")
            lines.append("")

        # Risk distribution
        if r.risk_distribution:
            lines += [
                "## Risk Category Distribution",
                "",
                "| Risk Category | Count |",
                "|---------------|-------|",
            ]
            for cat, cnt in sorted(r.risk_distribution.items()):
                lines.append(f"| {cat.replace('_', ' ').title()} | {cnt} |")
            lines.append("")

        # Company summaries table
        if r.company_summaries:
            lines += [
                "## Company-Level Summary",
                "",
                "| Company | ISIN | Sector | Direction | Mkt-Moving% | Impact Score | Risk Category |",
                "|---------|------|--------|-----------|-------------|--------------|---------------|",
            ]
            for cs in r.company_summaries:
                mm_pct = f"{cs.get('market_moving_probability', 0) * 100:.0f}%"
                lines.append(
                    f"| {cs.get('company_name', 'N/A')} "
                    f"| {cs.get('company_isin', 'N/A')} "
                    f"| {cs.get('sector', 'N/A')} "
                    f"| {cs.get('predicted_direction', 'N/A')} "
                    f"| {mm_pct} "
                    f"| {cs.get('impact_score', 0):.4f} "
                    f"| {cs.get('risk_category', 'N/A').replace('_', ' ').title()} |"
                )
            lines.append("")

        if r.disclaimer:
            lines += [
                "---",
                "",
                f"> **Disclaimer**: {r.disclaimer}",
                "",
            ]

        return "\n".join(lines)

    def _company_to_markdown(self, r: CompanyLevelReport) -> str:
        """Format a CompanyLevelReport as Markdown."""
        lines = [
            f"# Company Legislative Exposure Report",
            "",
            f"**Report ID**: `{r.report_id}`  ",
            f"**Company ISIN**: `{r.company_isin}`  ",
            f"**Company Name**: {r.company_name or 'N/A'}  ",
            f"**Sector**: {r.company_sector or 'N/A'}  ",
            f"**Report Version**: {r.report_version}  ",
            f"**Generated**: {r.generated_timestamp}",
            "",
            "---",
            "",
            "## Legislative Exposure Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Bills Analysed | {r.total_bills} |",
            f"| Bills with Positive Signal | {r.positive_bill_count} |",
            f"| Bills with Negative Signal | {r.negative_bill_count} |",
            f"| Bills with Neutral Signal | {r.neutral_bill_count} |",
            f"| Average Impact Score | {r.avg_impact_score:.4f} |",
            f"| Average Risk Score | {r.avg_risk_score:.4f} |",
            "",
        ]

        if r.high_impact_bills:
            lines += [
                "## High-Impact Bills",
                "",
            ]
            for b in r.high_impact_bills:
                lines.append(f"- `{b}`")
            lines.append("")

        if r.bill_summaries:
            lines += [
                "## Per-Bill Summary",
                "",
                "| Bill ID | Direction | Mkt-Moving% | Impact Score | Risk Category |",
                "|---------|-----------|-------------|--------------|---------------|",
            ]
            for bs in r.bill_summaries:
                mm_pct = f"{bs.get('market_moving_probability', 0) * 100:.0f}%"
                lines.append(
                    f"| {bs.get('bill_id', 'N/A')} "
                    f"| {bs.get('predicted_direction', 'N/A')} "
                    f"| {mm_pct} "
                    f"| {bs.get('impact_score', 0):.4f} "
                    f"| {bs.get('risk_category', 'N/A').replace('_', ' ').title()} |"
                )
            lines.append("")

        if r.disclaimer:
            lines += [
                "---",
                "",
                f"> **Disclaimer**: {r.disclaimer}",
                "",
            ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------

    def to_csv_summary(
        self,
        reports: list[AnyReport],
        report_type: str = "stakeholder",
    ) -> str:
        """
        Serialise a list of reports to a CSV summary string.

        Parameters
        ----------
        reports : list
            List of StakeholderReport, BillLevelReport, or CompanyLevelReport objects.
        report_type : str
            One of "stakeholder", "bill", "company". Used to select column set.

        Returns
        -------
        str
            CSV-formatted string (UTF-8 encoded).
        """
        if not reports:
            return ""

        output = io.StringIO()

        if report_type == "bill":
            writer = csv.DictWriter(output, fieldnames=_BILL_CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for r in reports:
                if not isinstance(r, BillLevelReport):
                    continue
                row = r.to_dict()
                row["sectors_affected"] = "; ".join(row.get("sectors_affected", []))
                writer.writerow({k: row.get(k, "") for k in _BILL_CSV_COLUMNS})

        elif report_type == "company":
            writer = csv.DictWriter(output, fieldnames=_COMPANY_CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for r in reports:
                if not isinstance(r, CompanyLevelReport):
                    continue
                row = r.to_dict()
                row["high_impact_bills"] = "; ".join(row.get("high_impact_bills", []))
                writer.writerow({k: row.get(k, "") for k in _COMPANY_CSV_COLUMNS})

        else:  # stakeholder (default)
            writer = csv.DictWriter(
                output, fieldnames=_STAKEHOLDER_CSV_COLUMNS, extrasaction="ignore"
            )
            writer.writeheader()
            for r in reports:
                if not isinstance(r, StakeholderReport):
                    continue
                row = r.to_dict()
                writer.writerow({k: row.get(k, "") for k in _STAKEHOLDER_CSV_COLUMNS})

        return output.getvalue()

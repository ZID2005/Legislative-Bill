"""
reporting/public_reporter.py
=============================
General-public-perspective report builder (Task 7.3).

Generates plain-English, jargon-free reports for the general public.

Language Rules
--------------
✓  Everyday language only
✓  Explain what a bill is in simple terms
✓  Avoid ML jargon, unexplained financial terms
✗  "SHAP values", "CAR", "gradient boosted trees"
✗  "Buy/Sell"
✗  "Guaranteed return"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.company import Company
from schemas.decision import DecisionSupportRecord
from schemas.report import (
    REPORT_DISCLAIMER,
    REPORT_METHODOLOGY_NOTE,
    REPORT_VERSION,
    StakeholderReport,
    StakeholderType,
    make_report_id,
)

logger = get_logger(__name__)

_PUBLIC_METHODOLOGY_NOTE = (
    "How we made this assessment: A computer system analysed historical data about how "
    "similar laws affected stock markets in the past. It identified patterns and used them "
    "to estimate what might happen when a new law is introduced. This is a research tool "
    "and its predictions can be wrong — it is not a substitute for professional advice."
)

_PUBLIC_DISCLAIMER = (
    "NOTICE: This summary is for general information and educational purposes only. "
    "It is produced by an academic research system and does not constitute financial, "
    "legal, or investment advice. The analysis may be incorrect. Always seek professional "
    "advice before making financial decisions."
)


class PublicReporter:
    """
    Builds plain-English, jargon-free StakeholderReport objects for the general public.
    """

    def __init__(self, report_version: str = REPORT_VERSION) -> None:
        self._report_version = report_version

    def build(
        self,
        decision: DecisionSupportRecord,
        bill: Optional[Bill] = None,
        company: Optional[Company] = None,
    ) -> StakeholderReport:
        """
        Build a StakeholderReport (PUBLIC type) from a DecisionSupportRecord.
        """
        report_id = make_report_id(
            decision.bill_id,
            decision.company_isin,
            decision.event_window,
            StakeholderType.PUBLIC.value,
        )

        bill_summary = self._build_bill_summary(decision, bill)
        company_summary = self._build_company_summary(decision, company)
        impact_summary = self._build_impact_summary(decision)
        risk_summary = self._build_risk_summary(decision)
        anticipation_summary = self._build_anticipation_summary(decision)
        confidence_summary = self._build_confidence_summary(decision)
        key_factors = self._build_key_factors(decision, bill)
        executive_summary = self._build_executive_summary(decision, bill, company)

        return StakeholderReport(
            report_id=report_id,
            bill_id=decision.bill_id,
            company_isin=decision.company_isin,
            event_window=decision.event_window,
            stakeholder_type=StakeholderType.PUBLIC.value,
            decision_version=decision.decision_version,
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            report_version=self._report_version,
            executive_summary=executive_summary,
            bill_summary=bill_summary,
            company_summary=company_summary,
            impact_summary=impact_summary,
            risk_summary=risk_summary,
            anticipation_summary=anticipation_summary,
            confidence_summary=confidence_summary,
            key_factors=key_factors,
            methodology_note=_PUBLIC_METHODOLOGY_NOTE,
            disclaimer=_PUBLIC_DISCLAIMER,
        )

    # ------------------------------------------------------------------

    def _build_executive_summary(
        self,
        d: DecisionSupportRecord,
        bill: Optional[Bill],
        company: Optional[Company],
    ) -> str:
        bill_title = (bill.title if bill else None) or d.bill_id
        ministry = (bill.ministry if bill else None) or "the government"
        comp_name = (company.company_name if company else None) or d.company_name or d.company_isin
        sector = (company.sector if company else None) or d.sector or "its sector"

        dir_name = d.predicted_direction.upper()
        if dir_name == "POSITIVE":
            impact_str = "could have a positive effect on the company's share price"
        elif dir_name == "NEGATIVE":
            impact_str = "could have a negative effect on the company's share price"
        else:
            impact_str = "is not expected to cause a large change in the company's share price"

        return (
            f"A proposed law called '{bill_title}', introduced by {ministry}, "
            f"{impact_str} of {comp_name} ({sector}). "
            f"This summary explains what the law is about and why it might matter."
        )

    def _build_bill_summary(
        self, d: DecisionSupportRecord, bill: Optional[Bill]
    ) -> str:
        """Plain-English explanation of what the bill is and why it matters."""
        bill_title = (bill.title if bill else None) or d.bill_id
        ministry = (bill.ministry if bill else None) or "the government"
        year = (bill.year if bill else None)
        summary_text = (bill.summary if bill else "") or ""
        sectors = (bill.sectors if bill else []) or []

        what_it_is = (
            f"'{bill_title}' is a proposed law (called a 'bill') put forward by {ministry}"
            + (f" in {year}" if year else "")
            + ". A bill must be approved by Parliament before it becomes a law."
        )

        if summary_text.strip() and len(summary_text.strip()) > 20:
            clean = summary_text.strip()
            if len(clean) > 500:
                clean = clean[:497] + "..."
            what_it_does = f"\nWhat it does: {clean}"
        else:
            what_it_does = (
                "\nWhat it does: This bill aims to update or introduce rules "
                "in a specific area of commerce or public policy."
            )

        sector_line = ""
        if sectors:
            sector_line = (
                f"\nAreas affected: This law is relevant to the following economic areas: "
                f"{', '.join(sectors)}."
            )

        return what_it_is + what_it_does + sector_line

    def _build_company_summary(
        self, d: DecisionSupportRecord, company: Optional[Company]
    ) -> str:
        """Plain-English company description."""
        name = (company.company_name if company else None) or d.company_name or d.company_isin
        sector = (company.sector if company else None) or d.sector or "its industry"
        cap_cat = (
            company.market_cap_category.value.replace("_", " ")
            if company else "N/A"
        )
        symbol = (company.ticker_nse if company else None) or d.company_symbol or "N/A"

        cap_desc = {
            "large cap": "one of India's largest companies",
            "mid cap": "a medium-sized Indian company",
            "small cap": "a smaller Indian company",
        }.get(cap_cat.lower(), "an Indian listed company")

        return (
            f"{name} (stock symbol: {symbol}) is {cap_desc} in the {sector} sector. "
            f"This report focuses on how the proposed legislation may affect this company."
        )

    def _build_impact_summary(self, d: DecisionSupportRecord) -> str:
        """Plain-English impact explanation — no financial jargon."""
        dir_name = d.predicted_direction.upper()
        mm_prob = d.market_moving_probability * 100
        impact_score_pct = d.impact_score * 100

        if dir_name == "POSITIVE":
            direction_desc = (
                "The computer model thinks this law could be good news for the company. "
                "This means share prices might rise, though this is not guaranteed."
            )
        elif dir_name == "NEGATIVE":
            direction_desc = (
                "The computer model thinks this law could be challenging for the company. "
                "This means share prices might fall, though this is not guaranteed."
            )
        else:
            direction_desc = (
                "The computer model thinks this law will not cause a big change for the company — "
                "the effect on share prices is expected to be small."
            )

        if mm_prob >= 70:
            mm_desc = f"There is a high chance ({mm_prob:.0f}%) that this law will noticeably affect the company's share price."
        elif mm_prob >= 50:
            mm_desc = f"There is a moderate chance ({mm_prob:.0f}%) that this law will affect the company's share price."
        else:
            mm_desc = f"There is a lower chance ({mm_prob:.0f}%) that this law will significantly move the company's share price."

        return (
            f"{direction_desc}\n\n"
            f"{mm_desc}\n\n"
            f"Overall estimated impact level: {impact_score_pct:.0f} out of 100 "
            f"(where higher means a larger potential effect)."
        )

    def _build_risk_summary(self, d: DecisionSupportRecord) -> str:
        """Plain-English risk explanation."""
        risk_cat = d.risk_category.replace("_", " ").title()

        risk_plain = {
            "Very Low": "The model is quite confident in its analysis — there is less uncertainty than usual.",
            "Low": "The model has reasonable confidence in this analysis.",
            "Moderate": "The model has some uncertainty in this analysis — treat the results with caution.",
            "High": "The model has significant uncertainty here — take these results as indicative only.",
            "Very High": "The model is quite uncertain. These results should be treated with considerable caution.",
        }.get(risk_cat, "Uncertainty level is unspecified.")

        pricing_risk = d.pricing_in_risk.replace("_", " ").lower()
        pricing_plain = (
            f"Market awareness level: {pricing_risk}. "
            "This indicates how much of the expected effect may have already been reflected in the share price "
            "before the law was officially announced."
        )

        return f"Reliability of this analysis: {risk_cat}\n{risk_plain}\n\n{pricing_plain}"

    def _build_anticipation_summary(self, d: DecisionSupportRecord) -> str:
        """Plain-English explanation of pre-event market activity."""
        a_class = d.anticipation_class

        public_interp = {
            "STRONG_EVIDENCE": (
                "There was notable activity in the company's share price before this law was announced. "
                "This suggests many investors may have expected the law in advance."
            ),
            "MODERATE_EVIDENCE": (
                "There was some unusual movement in the company's share price before this law was announced. "
                "This might mean some investors were anticipating the law."
            ),
            "WEAK_EVIDENCE": (
                "There was minor unusual activity in the share price before the announcement. "
                "It is unclear whether this was related to the law."
            ),
            "NO_EVIDENCE": (
                "The share price did not show unusual movements before the law was announced. "
                "The reaction — if any — is likely to happen around the time of the announcement."
            ),
            "NOT_ANALYZED": (
                "Pre-announcement market activity analysis was not performed for this company and law."
            ),
        }
        interp = public_interp.get(a_class, f"Market activity classification: {a_class}.")
        return f"Pre-announcement market activity: {interp}"

    def _build_confidence_summary(self, d: DecisionSupportRecord) -> str:
        """Plain-English confidence explanation."""
        conf_cat = d.predicted_confidence.replace("_", " ").lower()

        conf_plain = {
            "high": (
                "The computer model is fairly confident in this prediction — the input data was strong "
                "and the analysis produced a clear result."
            ),
            "medium": (
                "The computer model has moderate confidence — the analysis is reasonable but should "
                "be considered alongside other sources of information."
            ),
            "low": (
                "The computer model has low confidence in this prediction — the data signals were "
                "weak or mixed, and results should be treated with caution."
            ),
        }.get(conf_cat, f"Confidence level: {conf_cat}.")

        return f"How confident is the model? {conf_cat.title()}.\n{conf_plain}"

    def _build_key_factors(
        self, d: DecisionSupportRecord, bill: Optional[Bill]
    ) -> list[str]:
        """Plain-English key factors — no technical jargon."""
        factors: list[str] = []

        dir_name = d.predicted_direction.upper()
        if dir_name == "POSITIVE":
            factors.append("The law appears likely to benefit this type of company")
        elif dir_name == "NEGATIVE":
            factors.append("The law appears likely to create challenges for this type of company")
        else:
            factors.append("The law does not appear to strongly favour or harm this company")

        mm_prob = d.market_moving_probability
        if mm_prob >= 0.7:
            factors.append("High likelihood of noticeable share price movement")
        elif mm_prob >= 0.5:
            factors.append("Moderate likelihood of share price movement")
        else:
            factors.append("Lower likelihood of share price movement")

        a_class = d.anticipation_class
        if a_class in {"STRONG_EVIDENCE", "MODERATE_EVIDENCE"}:
            factors.append("Market participants appear to have already anticipated this law")
        elif a_class == "NO_EVIDENCE":
            factors.append("No signs of early market anticipation before the announcement")

        conf = d.predicted_confidence.lower()
        factors.append(f"Analytical confidence: {conf}")

        sectors = (bill.sectors if bill else []) or []
        if sectors:
            factors.append(f"Sectors potentially affected: {', '.join(sectors[:3])}")

        return factors

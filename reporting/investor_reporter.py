"""
reporting/investor_reporter.py
================================
Investor-perspective report builder (Task 7.3).

Transforms a DecisionSupportRecord into a StakeholderReport (type=INVESTOR)
using probabilistic, compliance-safe language.

Language Rules (Non-Negotiable)
--------------------------------
✓  "Model indicates a potential positive impact..."
✓  "Elevated market-moving probability observed..."
✓  "Analysis suggests..."
✗  "Stock will rise."
✗  "Guaranteed return."
✗  "Buy this stock."

This module does NOT modify predictions, risk scores, or model outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

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


class InvestorReporter:
    """
    Builds investor-perspective StakeholderReport objects from
    DecisionSupportRecord data.

    Parameters
    ----------
    report_version : str
        Semantic version of the reporting engine (propagated to reports).
    """

    def __init__(self, report_version: str = REPORT_VERSION) -> None:
        self._report_version = report_version

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def build(
        self,
        decision: DecisionSupportRecord,
        bill: Optional[Bill] = None,
        company: Optional[Company] = None,
        top_factors: Optional[list[str]] = None,
    ) -> StakeholderReport:
        """
        Build a StakeholderReport (INVESTOR type) from a DecisionSupportRecord.

        Parameters
        ----------
        decision : DecisionSupportRecord
            Upstream decision support record (Task 7.2 output).
        bill : Bill, optional
            Bill metadata for enrichment.
        company : Company, optional
            Company metadata for enrichment.
        top_factors : list[str], optional
            Top SHAP feature names for key_factors section.
            Falls back to narrative factors if None.

        Returns
        -------
        StakeholderReport
        """
        report_id = make_report_id(
            decision.bill_id,
            decision.company_isin,
            decision.event_window,
            StakeholderType.INVESTOR.value,
        )

        bill_summary = self._build_bill_summary(decision, bill)
        company_summary = self._build_company_summary(decision, company)
        impact_summary = self._build_impact_summary(decision)
        risk_summary = self._build_risk_summary(decision)
        anticipation_summary = self._build_anticipation_summary(decision)
        confidence_summary = self._build_confidence_summary(decision)
        key_factors = self._build_key_factors(decision, top_factors)
        executive_summary = self._build_executive_summary(decision)

        return StakeholderReport(
            report_id=report_id,
            bill_id=decision.bill_id,
            company_isin=decision.company_isin,
            event_window=decision.event_window,
            stakeholder_type=StakeholderType.INVESTOR.value,
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
            methodology_note=REPORT_METHODOLOGY_NOTE,
            disclaimer=REPORT_DISCLAIMER,
        )

    # ------------------------------------------------------------------
    # Section builders (private)
    # ------------------------------------------------------------------

    def _build_executive_summary(self, d: DecisionSupportRecord) -> str:
        """2–3 sentence executive summary using probabilistic language."""
        dir_name = d.predicted_direction.upper()
        dir_prob = d.direction_probability.get(dir_name, 0.0) * 100

        if dir_name == "POSITIVE":
            direction_str = f"potential positive market impact ({dir_prob:.1f}% directional probability)"
        elif dir_name == "NEGATIVE":
            direction_str = f"potential negative market impact ({dir_prob:.1f}% directional probability)"
        else:
            direction_str = f"subdued or neutral market reaction ({dir_prob:.1f}% neutral probability)"

        mm_prob = d.market_moving_probability * 100
        risk_label = d.risk_category.replace("_", " ").title()

        return (
            f"Model indicates a {direction_str} for {d.company_name or d.company_isin} "
            f"in response to the referenced legislation. "
            f"Market-moving probability is estimated at {mm_prob:.1f}% with an overall "
            f"impact score of {d.impact_score:.2f}. "
            f"Decision risk is classified as {risk_label} (score: {d.risk_score:.2f}). "
            f"This is an academic decision-support output — not investment advice."
        )

    def _build_bill_summary(
        self, d: DecisionSupportRecord, bill: Optional[Bill]
    ) -> str:
        """Bill identification and metadata section."""
        bill_title = (bill.title if bill else None) or d.bill_id
        ministry = (bill.ministry if bill else None) or "Government of India"
        bill_number = (bill.bill_number if bill else None) or "N/A"
        house = (bill.house.value if bill else None) or "N/A"
        intro_date = None
        if bill and bill.introduction_date:
            intro_date = bill.introduction_date.strftime("%d %B %Y")
        year = (bill.year if bill else None)
        status = (bill.status.value if bill else None) or "N/A"
        sectors = (bill.sectors if bill else None) or []

        parts = [
            f"Bill Title       : {bill_title}",
            f"Bill Number      : {bill_number}",
            f"Introduced By    : {ministry}",
            f"House of Origin  : {house.replace('_', ' ').title()}",
            f"Introduction Date: {intro_date or (str(year) if year else 'N/A')}",
            f"Legislative Status: {status.replace('_', ' ').title()}",
        ]
        if sectors:
            parts.append(f"Affected Sectors : {', '.join(sectors)}")

        return "\n".join(parts)

    def _build_company_summary(
        self, d: DecisionSupportRecord, company: Optional[Company]
    ) -> str:
        """Company identification and classification section."""
        name = (company.company_name if company else None) or d.company_name or d.company_isin
        sector = (company.sector if company else None) or d.sector or "N/A"
        industry = (company.industry if company else None) or "N/A"
        cap_cat = (
            company.market_cap_category.value.replace("_", " ").title()
            if company else "N/A"
        )
        symbol = (company.ticker_nse if company else None) or d.company_symbol or "N/A"

        return (
            f"Company Name      : {name}\n"
            f"ISIN              : {d.company_isin}\n"
            f"NSE Symbol        : {symbol}\n"
            f"Sector            : {sector}\n"
            f"Industry          : {industry}\n"
            f"Market Cap Tier   : {cap_cat}\n"
            f"Event Window      : {d.event_window}"
        )

    def _build_impact_summary(self, d: DecisionSupportRecord) -> str:
        """Direction, market-moving probability, and impact score section."""
        dir_name = d.predicted_direction.upper()
        pos_p = d.direction_probability.get("POSITIVE", 0.0) * 100
        neg_p = d.direction_probability.get("NEGATIVE", 0.0) * 100
        neu_p = d.direction_probability.get("NEUTRAL", 0.0) * 100
        mm_prob = d.market_moving_probability * 100
        strength = d.predicted_impact_strength.replace("_", " ").title()
        impact_cat = d.impact_category.replace("_", " ").title()

        if dir_name == "POSITIVE":
            dir_line = (
                f"Predicted Direction      : Potential Positive Impact "
                f"({pos_p:.1f}% probability)"
            )
        elif dir_name == "NEGATIVE":
            dir_line = (
                f"Predicted Direction      : Potential Negative Impact "
                f"({neg_p:.1f}% probability)"
            )
        else:
            dir_line = (
                f"Predicted Direction      : Neutral / Subdued Reaction "
                f"({neu_p:.1f}% neutral probability)"
            )

        return (
            f"{dir_line}\n"
            f"Direction Distribution   : Positive {pos_p:.0f}% | Negative {neg_p:.0f}% | Neutral {neu_p:.0f}%\n"
            f"Market-Moving Probability: {mm_prob:.1f}%\n"
            f"Impact Strength Tier     : {strength}\n"
            f"Impact Category          : {impact_cat}\n"
            f"Overall Impact Score     : {d.impact_score:.4f} (range 0.0–1.0)"
        )

    def _build_risk_summary(self, d: DecisionSupportRecord) -> str:
        """Risk score, risk category, and pricing-in risk section."""
        risk_cat = d.risk_category.replace("_", " ").title()
        pricing_risk = d.pricing_in_risk.replace("_", " ").title()

        return (
            f"Decision Risk Score : {d.risk_score:.4f} (range 0.0–1.0)\n"
            f"Risk Category       : {risk_cat}\n"
            f"Pricing-In Risk     : {pricing_risk}\n"
            f"Pricing-In Score    : {d.pricing_in_score:.4f}"
        )

    def _build_anticipation_summary(self, d: DecisionSupportRecord) -> str:
        """Anticipation classification and score interpretation."""
        a_class = d.anticipation_class
        a_score = d.anticipation_score

        classification_labels = {
            "STRONG_EVIDENCE": (
                "Strong pre-event market activity detected — analysis suggests a substantial portion "
                "of the expected market reaction may already be reflected in current prices."
            ),
            "MODERATE_EVIDENCE": (
                "Moderate pre-event trading signals observed — partial pricing-in is plausible, "
                "implying the anticipated reaction may be partially absorbed prior to the event window."
            ),
            "WEAK_EVIDENCE": (
                "Weak pre-event signals observed — limited evidence of market anticipation. "
                "The predicted reaction may materialise more fully around the event window."
            ),
            "NO_EVIDENCE": (
                "No significant pre-event market activity detected — analysis does not indicate "
                "prior pricing-in of the anticipated legislative impact."
            ),
            "NOT_ANALYZED": (
                "Anticipation analysis was not performed for this observation."
            ),
        }
        interp = classification_labels.get(
            a_class,
            f"Anticipation classification: {a_class}."
        )

        return (
            f"Anticipation Classification: {a_class.replace('_', ' ').title()}\n"
            f"Anticipation Score         : {a_score:.4f} (range 0.0–1.0)\n"
            f"Interpretation             : {interp}"
        )

    def _build_confidence_summary(self, d: DecisionSupportRecord) -> str:
        """Model confidence tier and scalar score."""
        conf_cat = d.predicted_confidence.replace("_", " ").title()
        conf_prob = d.confidence_probability
        high_p = conf_prob.get("HIGH", 0.0) * 100
        med_p = conf_prob.get("MEDIUM", 0.0) * 100
        low_p = conf_prob.get("LOW", 0.0) * 100

        return (
            f"Model Confidence Tier : {conf_cat}\n"
            f"Confidence Score      : {d.confidence_score:.4f} (range 0.0–1.0)\n"
            f"Confidence Distribution: High {high_p:.0f}% | Medium {med_p:.0f}% | Low {low_p:.0f}%"
        )

    def _build_key_factors(
        self, d: DecisionSupportRecord, top_factors: Optional[list[str]]
    ) -> list[str]:
        """
        Build key_factors list.

        Uses SHAP feature names if available; falls back to extracting
        narrative factors from the decision_reason field.
        """
        if top_factors:
            return [f"Model factor: {f}" for f in top_factors[:10]]

        # Fallback: extract structured factors from decision_reason
        factors: list[str] = []

        dir_name = d.predicted_direction.upper()
        dir_prob = d.direction_probability.get(dir_name, 0.0)
        factors.append(
            f"Directional signal: {dir_name} with {dir_prob*100:.1f}% probability"
        )

        mm_prob = d.market_moving_probability
        if mm_prob >= 0.70:
            factors.append(f"High market-moving probability ({mm_prob*100:.1f}%)")
        elif mm_prob >= 0.50:
            factors.append(f"Elevated market-moving probability ({mm_prob*100:.1f}%)")
        else:
            factors.append(f"Moderate market-moving probability ({mm_prob*100:.1f}%)")

        factors.append(
            f"Impact strength: {d.predicted_impact_strength.replace('_', ' ').title()}"
        )
        factors.append(
            f"Model confidence: {d.predicted_confidence.replace('_', ' ').title()} "
            f"(score: {d.confidence_score:.2f})"
        )

        a_class = d.anticipation_class
        if a_class not in {"NOT_ANALYZED", "NO_EVIDENCE"}:
            factors.append(
                f"Pre-event anticipation detected: {a_class.replace('_', ' ').title()} "
                f"(score: {d.anticipation_score:.2f})"
            )

        factors.append(f"Risk category: {d.risk_category.replace('_', ' ').title()}")
        return factors

"""
reporting/business_reporter.py
================================
Business/Corporate-perspective report builder (Task 7.3).

Transforms a DecisionSupportRecord into a StakeholderReport (type=BUSINESS)
focused on regulatory, operational, and strategic language — not trading language.

Language Rules
--------------
✓  "Potential operational implications..."
✓  "Regulatory compliance considerations..."
✓  "Knowledge-layer mapping identifies direct exposure..."
✗  "Stock will move."
✗  "Buy/Sell signal."
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.company import Company
from schemas.decision import DecisionSupportRecord
from schemas.mapping_record import BillCompanyMapping
from schemas.report import (
    REPORT_DISCLAIMER,
    REPORT_METHODOLOGY_NOTE,
    REPORT_VERSION,
    StakeholderReport,
    StakeholderType,
    make_report_id,
)

logger = get_logger(__name__)


class BusinessReporter:
    """
    Builds business/corporate-perspective StakeholderReport objects.

    Parameters
    ----------
    report_version : str
    """

    def __init__(self, report_version: str = REPORT_VERSION) -> None:
        self._report_version = report_version

    def build(
        self,
        decision: DecisionSupportRecord,
        bill: Optional[Bill] = None,
        company: Optional[Company] = None,
        mapping: Optional[BillCompanyMapping] = None,
    ) -> StakeholderReport:
        """
        Build a StakeholderReport (BUSINESS type) from a DecisionSupportRecord.
        """
        report_id = make_report_id(
            decision.bill_id,
            decision.company_isin,
            decision.event_window,
            StakeholderType.BUSINESS.value,
        )

        bill_summary = self._build_bill_summary(decision, bill)
        company_summary = self._build_company_summary(decision, company)
        impact_summary = self._build_impact_summary(decision, mapping)
        risk_summary = self._build_risk_summary(decision)
        anticipation_summary = self._build_anticipation_summary(decision)
        confidence_summary = self._build_confidence_summary(decision)
        key_factors = self._build_key_factors(decision)
        executive_summary = self._build_executive_summary(decision, bill, company)

        return StakeholderReport(
            report_id=report_id,
            bill_id=decision.bill_id,
            company_isin=decision.company_isin,
            event_window=decision.event_window,
            stakeholder_type=StakeholderType.BUSINESS.value,
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

    def _build_executive_summary(
        self,
        d: DecisionSupportRecord,
        bill: Optional[Bill],
        company: Optional[Company],
    ) -> str:
        bill_title = (bill.title if bill else None) or d.bill_id
        ministry = (bill.ministry if bill else None) or "Government of India"
        comp_name = (company.company_name if company else None) or d.company_name or d.company_isin
        sector = (company.sector if company else None) or d.sector or "its sector"

        dir_name = d.predicted_direction.upper()
        if dir_name == "POSITIVE":
            impact_str = "potential positive business implications"
        elif dir_name == "NEGATIVE":
            impact_str = "potential adverse business implications"
        else:
            impact_str = "manageable neutral operational implications"

        conf = d.predicted_confidence.replace("_", " ").lower()
        return (
            f"Legislative analysis indicates that '{bill_title}' introduced by {ministry} "
            f"presents {impact_str} for {comp_name} ({sector}). "
            f"Quantitative modelling confidence is assessed as {conf}. "
            f"The following sections detail regulatory, operational, and market-impact considerations."
        )

    def _build_bill_summary(
        self, d: DecisionSupportRecord, bill: Optional[Bill]
    ) -> str:
        bill_title = (bill.title if bill else None) or d.bill_id
        ministry = (bill.ministry if bill else None) or "Government of India"
        bill_number = (bill.bill_number if bill else None) or "N/A"
        house = (bill.house.value if bill else None) or "N/A"
        status = (bill.status.value if bill else None) or "N/A"
        session = (bill.session if bill else None) or "N/A"
        summary_text = (bill.summary if bill else "") or ""
        sectors = (bill.sectors if bill else []) or []
        keywords = (bill.keywords if bill else []) or []
        related_acts = (bill.related_acts if bill else []) or []

        year = (bill.year if bill else None)
        intro_date = None
        if bill and bill.introduction_date:
            intro_date = bill.introduction_date.strftime("%d %B %Y")

        lines = [
            f"Bill Title       : {bill_title}",
            f"Bill Number      : {bill_number}",
            f"Ministry / Dept  : {ministry}",
            f"House of Origin  : {house.replace('_', ' ').title()}",
            f"Introduction Date: {intro_date or (str(year) if year else 'N/A')}",
            f"Parliamentary Session: {session}",
            f"Legislative Status: {status.replace('_', ' ').title()}",
        ]
        if sectors:
            lines.append(f"Regulatory Domains: {', '.join(sectors)}")
        if keywords:
            lines.append(f"Key Themes       : {', '.join(keywords[:8])}")
        if related_acts:
            lines.append(f"Related Acts     : {', '.join(related_acts[:5])}")
        if summary_text.strip():
            # Truncate long summaries for the bill summary section
            clean = summary_text.strip()
            if len(clean) > 600:
                clean = clean[:597] + "..."
            lines.append(f"\nBill Purpose     :\n{clean}")
        return "\n".join(lines)

    def _build_company_summary(
        self, d: DecisionSupportRecord, company: Optional[Company]
    ) -> str:
        name = (company.company_name if company else None) or d.company_name or d.company_isin
        sector = (company.sector if company else None) or d.sector or "N/A"
        industry = (company.industry if company else None) or "N/A"
        sub_industry = (company.sub_industry if company else None) or "N/A"
        cap_cat = (
            company.market_cap_category.value.replace("_", " ").title()
            if company else "N/A"
        )
        symbol = (company.ticker_nse if company else None) or d.company_symbol or "N/A"
        hq_city = (company.hq_city if company else None) or "N/A"
        hq_state = (company.hq_state if company else None) or "N/A"

        return (
            f"Company Name      : {name}\n"
            f"ISIN              : {d.company_isin}\n"
            f"NSE Symbol        : {symbol}\n"
            f"Sector            : {sector}\n"
            f"Industry Group    : {industry}\n"
            f"Sub-Industry      : {sub_industry}\n"
            f"Market Cap Tier   : {cap_cat}\n"
            f"Headquarters      : {hq_city}, {hq_state}\n"
            f"Event Window      : {d.event_window}"
        )

    def _build_impact_summary(
        self, d: DecisionSupportRecord, mapping: Optional[BillCompanyMapping]
    ) -> str:
        """
        Operational, regulatory, and market-impact implications in business language.
        """
        dir_name = d.predicted_direction.upper()
        strength = d.predicted_impact_strength.replace("_", " ").title()

        if dir_name == "POSITIVE":
            operational = (
                "Potential operational tailwinds: the legislation may create favourable conditions "
                "such as regulatory clarity, expanded market access, or structural incentives for "
                "entities in this sector."
            )
            regulatory = (
                "Regulatory implications appear constructive. Compliance burden is not expected to "
                "materially increase; potential for streamlined administrative frameworks."
            )
            market = (
                f"Market-impact modelling indicates a potential positive price signal "
                f"(market-moving probability: {d.market_moving_probability*100:.1f}%, "
                f"impact strength: {strength})."
            )
        elif dir_name == "NEGATIVE":
            operational = (
                "Potential operational headwinds: the legislation may introduce heightened compliance "
                "costs, margin compression, operational restructuring requirements, or tighter "
                "supervisory constraints on business activities."
            )
            regulatory = (
                "Regulatory implications appear challenging. Businesses in the affected sector may "
                "need to review compliance frameworks, internal controls, and statutory obligations."
            )
            market = (
                f"Market-impact modelling indicates a potential adverse price signal "
                f"(market-moving probability: {d.market_moving_probability*100:.1f}%, "
                f"impact strength: {strength})."
            )
        else:
            operational = (
                "Operational implications appear neutral. The legislation is modelled to introduce "
                "manageable administrative adjustments with limited net impact on core business operations."
            )
            regulatory = (
                "Regulatory implications are assessed as neutral. Standard compliance updates "
                "may be required, but no significant structural burden is anticipated."
            )
            market = (
                f"Market-impact modelling indicates a subdued price signal "
                f"(market-moving probability: {d.market_moving_probability*100:.1f}%, "
                f"impact strength: {strength})."
            )

        # Mapping exposure context
        exposure_text = ""
        if mapping:
            confidence = float(getattr(mapping, "mapping_confidence", 0.80) or 0.80)
            reason = str(getattr(mapping, "mapping_reason", "") or "")
            exposure_text = (
                f"\nKnowledge-layer mapping identifies a relevance confidence of "
                f"{confidence:.2f} for this company-bill pairing."
            )
            if reason.strip():
                exposure_text += f" Mapping context: {reason.strip()}"

        return (
            f"Operational Implications:\n{operational}\n\n"
            f"Regulatory Implications:\n{regulatory}\n\n"
            f"Market Implications:\n{market}"
            f"{exposure_text}"
        )

    def _build_risk_summary(self, d: DecisionSupportRecord) -> str:
        risk_cat = d.risk_category.replace("_", " ").title()
        pricing_risk = d.pricing_in_risk.replace("_", " ").title()

        risk_interp = {
            "VERY LOW": "Minimal model uncertainty; high analytical confidence.",
            "LOW": "Low model uncertainty; results are considered reliable.",
            "MODERATE": "Moderate model uncertainty; results should be interpreted with caution.",
            "HIGH": "Elevated model uncertainty; results are indicative only.",
            "VERY HIGH": (
                "High model uncertainty; results carry significant caveats and "
                "should not be used as the sole basis for business decisions."
            ),
        }.get(risk_cat, "Model uncertainty level not determinable.")

        return (
            f"Decision Risk Category : {risk_cat}\n"
            f"Decision Risk Score    : {d.risk_score:.4f} (range 0.0–1.0)\n"
            f"Risk Interpretation    : {risk_interp}\n"
            f"Pricing-In Risk        : {pricing_risk} — reflects degree of market awareness "
            f"already incorporated into prices prior to the event window.\n"
            f"Pricing-In Score       : {d.pricing_in_score:.4f}"
        )

    def _build_anticipation_summary(self, d: DecisionSupportRecord) -> str:
        a_class = d.anticipation_class
        a_score = d.anticipation_score

        business_interp = {
            "STRONG_EVIDENCE": (
                "Substantial pre-event market movement suggests the legislative impact was "
                "broadly anticipated by market participants. Business planning may benefit from "
                "proactive engagement with the emerging regulatory landscape."
            ),
            "MODERATE_EVIDENCE": (
                "Moderate pre-event market signals suggest partial anticipation. Businesses "
                "should monitor regulatory developments and prepare contingency frameworks."
            ),
            "WEAK_EVIDENCE": (
                "Limited pre-event market signals. The legislation's business impact is likely "
                "to materialise within the standard event window, allowing time for preparation."
            ),
            "NO_EVIDENCE": (
                "No significant pre-event market activity. The business impact is likely to "
                "unfold around the event date, providing lead time for strategic adjustment."
            ),
            "NOT_ANALYZED": (
                "Pre-event market analysis was not performed for this observation."
            ),
        }
        interp = business_interp.get(a_class, f"Classification: {a_class}.")

        return (
            f"Market Awareness Classification: {a_class.replace('_', ' ').title()}\n"
            f"Anticipation Score            : {a_score:.4f} (range 0.0–1.0)\n"
            f"Business Context              : {interp}"
        )

    def _build_confidence_summary(self, d: DecisionSupportRecord) -> str:
        conf_cat = d.predicted_confidence.replace("_", " ").title()
        return (
            f"Analytical Confidence Level: {conf_cat}\n"
            f"Confidence Score           : {d.confidence_score:.4f} (range 0.0–1.0)\n"
            f"Note: Confidence reflects the quantitative model's internal consistency "
            f"and the signal strength of input features — not a guarantee of accuracy."
        )

    def _build_key_factors(self, d: DecisionSupportRecord) -> list[str]:
        """Business-relevant key factors derived from decision record."""
        factors: list[str] = []

        dir_name = d.predicted_direction.upper()
        if dir_name == "POSITIVE":
            factors.append("Legislative direction: constructive regulatory signal for sector")
        elif dir_name == "NEGATIVE":
            factors.append("Legislative direction: restrictive or cost-increasing regulatory signal")
        else:
            factors.append("Legislative direction: neutral regulatory adjustment anticipated")

        factors.append(
            f"Sector impact magnitude: {d.predicted_impact_strength.replace('_', ' ').title()}"
        )
        factors.append(
            f"Market awareness level: {d.anticipation_class.replace('_', ' ').title()}"
        )
        factors.append(
            f"Analytical confidence: {d.predicted_confidence.replace('_', ' ').title()} "
            f"(score: {d.confidence_score:.2f})"
        )
        factors.append(
            f"Decision risk level: {d.risk_category.replace('_', ' ').title()} "
            f"(score: {d.risk_score:.2f})"
        )
        return factors

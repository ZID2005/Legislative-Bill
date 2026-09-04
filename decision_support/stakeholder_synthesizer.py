"""
decision_support/stakeholder_synthesizer.py
===========================================
Multi-stakeholder decision narrative synthesizer (Task 7.2).

Generates three tailored, structured decision-support perspectives:
1. **Investor View**: Direction probability distribution, market-moving likelihood,
   impact strength tier, model confidence, and pricing-in / anticipation dynamics.
2. **Business View**: Affected industry sector, company mapping exposure, regulatory
   relevance, and operational/competitive implications.
3. **General Public View**: Plain-English, jargon-free explanation of the legislative bill
   and its broader societal and commercial purpose.

Compliance & Governance
-----------------------
- Adheres strictly to probabilistic language: "potential positive impact", "potential negative impact",
  "elevated market-moving probability", "model indicates", "estimated confidence", "evidence suggests".
- Never guarantees stock price movements.
- Never characterizes pre-event market anticipation as insider trading or illegal activity.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from schemas.anticipation import AnticipationClassification
from schemas.bill import Bill
from schemas.company import Company
from schemas.mapping_record import BillCompanyMapping
from schemas.prediction import PredictionRecord

logger = get_logger(__name__)

DISCLAIMER_TEXT = (
    "Probabilistic academic decision support for quantitative research purposes only. "
    "Does not guarantee future price movements or constitute investment advice."
)


class StakeholderSynthesizer:
    """
    Synthesizes tailored qualitative decision-support narratives for investors,
    business executives, and the general public.
    """

    def generate_investor_summary(
        self,
        prediction: PredictionRecord,
        impact_score: float,
        risk_score: float,
        risk_category: str,
        pricing_in_risk: str,
    ) -> str:
        """
        Synthesize structured perspective for institutional and retail investors.
        """
        dir_name = prediction.predicted_direction.upper()
        dir_prob = prediction.direction_probability.get(dir_name, 0.50)
        mm_prob = prediction.market_moving_probability
        strength = prediction.predicted_impact_strength
        conf_cat = prediction.predicted_confidence
        a_score = prediction.anticipation_score
        a_class = prediction.anticipation_class

        parts: list[str] = []

        # 1. Direction and Conviction
        if dir_name == "POSITIVE":
            parts.append(
                f"Model indicates a potential positive impact with {dir_prob*100:.1f}% directional probability "
                f"(Distribution: {prediction.direction_probability.get('POSITIVE', 0.0)*100:.0f}% Positive, "
                f"{prediction.direction_probability.get('NEGATIVE', 0.0)*100:.0f}% Negative, "
                f"{prediction.direction_probability.get('NEUTRAL', 0.0)*100:.0f}% Neutral)."
            )
        elif dir_name == "NEGATIVE":
            parts.append(
                f"Model indicates a potential negative impact with {dir_prob*100:.1f}% directional probability "
                f"(Distribution: {prediction.direction_probability.get('NEGATIVE', 0.0)*100:.0f}% Negative, "
                f"{prediction.direction_probability.get('POSITIVE', 0.0)*100:.0f}% Positive, "
                f"{prediction.direction_probability.get('NEUTRAL', 0.0)*100:.0f}% Neutral)."
            )
        else:
            parts.append(
                f"Model indicates a neutral or subdued market reaction ({dir_prob*100:.1f}% neutral probability; "
                f"{prediction.direction_probability.get('POSITIVE', 0.0)*100:.0f}% Positive, "
                f"{prediction.direction_probability.get('NEGATIVE', 0.0)*100:.0f}% Negative)."
            )

        # 2. Market-moving and Impact Strength
        if prediction.predicted_market_moving or mm_prob >= 0.50:
            parts.append(
                f"Analysis suggests an elevated market-moving probability ({mm_prob*100:.1f}%) "
                f"with {strength.lower()} impact strength tier and estimated {conf_cat.lower()} confidence."
            )
        else:
            parts.append(
                f"Analysis suggests a low market-moving probability ({mm_prob*100:.1f}%), "
                f"consistent with a {strength.lower()} magnitude expectation and {conf_cat.lower()} model confidence."
            )

        # 3. Pricing-in / Anticipation Dynamics
        if a_class in {AnticipationClassification.STRONG_EVIDENCE.value, "STRONG_EVIDENCE"} or a_score >= 0.75:
            parts.append(
                f"Substantial pre-event market activity suggests part or all of the expected reaction "
                f"may already be priced in (Anticipation Score: {a_score:.2f}, Pricing-In Risk: {pricing_in_risk})."
            )
        elif a_class in {AnticipationClassification.MODERATE_EVIDENCE.value, "MODERATE_EVIDENCE"} or a_score >= 0.50:
            parts.append(
                f"Moderate pre-event trading signals suggest partial pricing-in is plausible "
                f"(Anticipation Score: {a_score:.2f}, Pricing-In Risk: {pricing_in_risk})."
            )
        else:
            parts.append(
                f"Limited pre-event evidence suggests a larger portion of the predicted reaction "
                f"may occur around the event window rather than having been previously absorbed (Anticipation Score: {a_score:.2f})."
            )

        # 4. Overall Decision Risk
        parts.append(
            f"Overall decision risk score is estimated at {risk_score:.2f} ({risk_category.replace('_', ' ').title()}), "
            f"reflecting composite model uncertainty and pricing-in exposure."
        )

        return " ".join(parts)

    def generate_business_summary(
        self,
        prediction: PredictionRecord,
        company: Optional[Company] = None,
        bill: Optional[Bill] = None,
        mapping: Optional[BillCompanyMapping] = None,
    ) -> str:
        """
        Synthesize structured perspective for corporate leadership and strategy teams.
        """
        comp_name = (
            (company.company_name if company else None)
            or prediction.company_name
            or prediction.company_isin
        )
        comp_sector = (company.sector if company else None) or "Core Sector"
        comp_industry = (company.industry if company else None) or "Commercial Enterprises"
        bill_title = (bill.title if bill else None) or prediction.bill_id
        ministry = (bill.ministry if bill else None) or "Government of India"

        parts: list[str] = []

        parts.append(
            f"From a corporate perspective, '{bill_title}' introduced by the {ministry} directly intersects "
            f"with {comp_name} ({comp_sector} / {comp_industry})."
        )

        # Exposure and Regulatory Relevance
        if mapping:
            comp_entry = None
            for c in getattr(mapping, "candidate_companies", []):
                if isinstance(c, dict) and (
                    c.get("isin") == prediction.company_isin
                    or c.get("company_isin") == prediction.company_isin
                ):
                    comp_entry = c
                    break

            relevance = (
                float(comp_entry.get("confidence") or comp_entry.get("relevance_score", 0.85))
                if comp_entry
                else float(getattr(mapping, "mapping_confidence", 0.85) or 0.85)
            )
            exp_type = (
                str(comp_entry.get("exposure_type", "direct"))
                if comp_entry
                else "direct"
            )
            reason = (
                str(comp_entry.get("reason") or comp_entry.get("reasoning") or getattr(mapping, "mapping_reason", ""))
                if comp_entry
                else str(getattr(mapping, "mapping_reason", ""))
            )

            parts.append(
                f"Knowledge-layer mapping identifies an exposure relevance of {relevance:.2f} "
                f"with {exp_type.lower()} alignment."
            )
            if reason:
                clean_reasoning = reason.strip()
                if not clean_reasoning.endswith("."):
                    clean_reasoning += "."
                parts.append(f"Strategic context: {clean_reasoning}")
        else:
            parts.append(
                f"The legislation presents direct regulatory relevance to operating conditions and compliance frameworks in the {comp_sector} industry."
            )

        # Business Implications
        dir_name = prediction.predicted_direction.upper()
        if dir_name == "POSITIVE":
            parts.append(
                f"Model evidence suggests potential positive business implications, such as structural tailwinds, "
                f"regulatory clarity, or expanded operational scope."
            )
        elif dir_name == "NEGATIVE":
            parts.append(
                f"Model evidence suggests potential negative business implications, including heightened compliance costs, "
                f"margin compression, or tighter supervisory constraints."
            )
        else:
            parts.append(
                f"Model evidence suggests neutral net business implications with manageable operational or statutory adjustments."
            )

        return " ".join(parts)

    def generate_public_summary(
        self,
        bill: Optional[Bill] = None,
        prediction: Optional[PredictionRecord] = None,
    ) -> str:
        """
        Synthesize plain-English, jargon-free summary for the general public.
        """
        if bill:
            bill_title = getattr(bill, "title", prediction.bill_id if prediction else "the legislation")
            ministry = getattr(bill, "ministry", "") or "Government of India"
            summary_text = (getattr(bill, "summary", "") or getattr(bill, "description", "") or "").strip()
        else:
            bill_title = prediction.bill_id if prediction else "the legislation"
            ministry = "Government of India"
            summary_text = ""

        parts: list[str] = []

        parts.append(
            f"'{bill_title}' is a proposed legislative measure introduced by {ministry}."
        )

        if summary_text and len(summary_text.strip()) > 20:
            clean_summary = summary_text.strip()
            if not clean_summary.endswith("."):
                clean_summary += "."
            parts.append(clean_summary)
        else:
            parts.append(
                "The bill seeks to reform, clarify, and modernize statutory frameworks governing the sector, "
                "aiming to ensure consumer protection, operational transparency, and standardized administrative oversight."
            )

        parts.append(
            "This public intelligence overview aims to explain the legislative intent clearly without financial or market jargon."
        )

        return " ".join(parts)

    def synthesize_decision_reason(
        self,
        prediction: PredictionRecord,
        impact_score: float,
        risk_score: float,
        risk_category: str,
        pricing_in_risk: str,
        investor_summary: str,
    ) -> str:
        """
        Synthesize the primary decision narrative unifying prediction, scores, and compliance disclaimer.
        """
        dir_name = prediction.predicted_direction.lower()
        strength = prediction.predicted_impact_strength.lower()
        conf = prediction.predicted_confidence.lower()

        narrative = (
            f"Decision support assessment indicates a potential {dir_name} market impact ({strength} magnitude tier, "
            f"{conf} model confidence). Deterministic Impact Score is {impact_score:.2f} and Decision Risk is {risk_score:.2f} "
            f"({risk_category.replace('_', ' ').title()}). Pricing-in risk is evaluated as {pricing_in_risk}. "
            f"[{DISCLAIMER_TEXT}]"
        )
        return narrative

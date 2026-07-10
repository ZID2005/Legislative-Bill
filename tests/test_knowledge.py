"""
tests/test_knowledge.py
========================
Unit tests for the knowledge loader.

Verifies that all knowledge CSVs load correctly and the loader functions
return plausible, well-structured data.
"""

from __future__ import annotations


class TestKnowledgeLoader:
    """Tests for knowledge.loader functions."""

    def test_list_ministries_not_empty(self) -> None:
        from knowledge.loader import list_ministries

        ministries = list_ministries()
        assert len(ministries) > 0

    def test_get_ministry_sectors_finance(self) -> None:
        from knowledge.loader import get_ministry_sectors

        sectors = get_ministry_sectors("Ministry of Finance")
        assert isinstance(sectors, list)
        assert len(sectors) > 0
        assert "Banking & Financial Services" in sectors

    def test_get_ministry_sectors_unknown_returns_empty(self) -> None:
        from knowledge.loader import get_ministry_sectors

        result = get_ministry_sectors("Ministry of Magic")
        assert result == []

    def test_list_sectors_not_empty(self) -> None:
        from knowledge.loader import list_sectors

        sectors = list_sectors()
        assert len(sectors) > 5

    def test_get_sector_keywords_banking(self) -> None:
        from knowledge.loader import get_sector_keywords

        keywords = get_sector_keywords("Banking & Financial Services")
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should contain core banking keywords
        assert any("bank" in kw.lower() for kw in keywords)

    def test_get_sector_keywords_unknown_returns_empty(self) -> None:
        from knowledge.loader import get_sector_keywords

        result = get_sector_keywords("Nonexistent Sector XYZ")
        assert result == []

    def test_get_policy_keywords_not_empty(self) -> None:
        from knowledge.loader import get_policy_keywords

        policies = get_policy_keywords()
        assert isinstance(policies, list)
        assert len(policies) > 0
        # Each row should have the required keys
        for row in policies:
            assert "policy_type" in row
            assert "keywords" in row
            assert "likely_impact_direction" in row

    def test_get_policy_keywords_impact_values(self) -> None:
        from knowledge.loader import get_policy_keywords

        valid_impacts = {"positive", "negative", "mixed"}
        for row in get_policy_keywords():
            assert row["likely_impact_direction"].lower() in valid_impacts

    def test_get_bill_category_finance_bill(self) -> None:
        from knowledge.loader import get_bill_category

        result = get_bill_category("The Finance Bill, 2024")
        assert result is not None
        assert "primary_sector" in result

    def test_get_bill_category_no_match(self) -> None:
        from knowledge.loader import get_bill_category

        result = get_bill_category("Some Completely Unknown Regulation Bill 2024")
        # Should return None gracefully (not raise)
        assert result is None or isinstance(result, dict)

    def test_get_company_sector_override_known_isin(self) -> None:
        from knowledge.loader import get_company_sector_override

        result = get_company_sector_override("INE009A01021")  # Infosys
        assert result == "Technology & IT Services"

    def test_get_company_sector_override_unknown_isin(self) -> None:
        from knowledge.loader import get_company_sector_override

        result = get_company_sector_override("INE000000000")
        assert result is None

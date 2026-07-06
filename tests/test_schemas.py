"""
tests/test_schemas.py
=====================
Unit tests for the schemas package.

Verifies that Bill, Company, PriceRecord, and Prediction schemas:
*  Can be instantiated with required fields
*  Serialise to dicts correctly (to_dict)
*  Deserialise from dicts correctly (from_dict round-trip)
*  Enum values behave as expected
"""

from __future__ import annotations

from datetime import date, datetime


class TestBillSchema:
    """Tests for schemas.bill.Bill"""

    def _make_bill(self) -> object:
        from schemas.bill import Bill, BillHouse, BillStatus
        return Bill(
            bill_id="finance-bill-2024",
            title="The Finance Bill, 2024",
            year=2024,
            ministry="Ministry of Finance",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.PASSED_BOTH,
            url="https://prsindia.org/bills/finance-bill-2024",
        )

    def test_bill_instantiation(self) -> None:
        bill = self._make_bill()
        assert bill.bill_id == "finance-bill-2024"
        assert bill.year == 2024

    def test_bill_defaults(self) -> None:
        bill = self._make_bill()
        assert bill.sectors == []
        assert bill.keywords == []
        assert bill.summary == ""
        assert bill.introduction_date is None

    def test_bill_to_dict(self) -> None:
        bill = self._make_bill()
        d = bill.to_dict()
        assert d["bill_id"] == "finance-bill-2024"
        assert d["house"] == "lok_sabha"
        assert d["status"] == "passed_both"
        assert isinstance(d["sectors"], list)

    def test_bill_from_dict_roundtrip(self) -> None:
        from schemas.bill import Bill
        bill = self._make_bill()
        d = bill.to_dict()
        restored = Bill.from_dict(d)
        assert restored.bill_id == bill.bill_id
        assert restored.year == bill.year
        assert restored.house == bill.house
        assert restored.status == bill.status

    def test_bill_status_enum_values(self) -> None:
        from schemas.bill import BillStatus
        assert BillStatus.PASSED_BOTH.value == "passed_both"
        assert BillStatus.LAPSED.value == "lapsed"

    def test_bill_house_enum_values(self) -> None:
        from schemas.bill import BillHouse
        assert BillHouse.LOK_SABHA.value == "lok_sabha"
        assert BillHouse.RAJYA_SABHA.value == "rajya_sabha"

    def test_bill_repr(self) -> None:
        bill = self._make_bill()
        assert "finance-bill-2024" in repr(bill)


class TestCompanySchema:
    """Tests for schemas.company.Company"""

    def _make_company(self) -> object:
        from schemas.company import Company
        return Company(
            isin="INE009A01021",
            company_name="Infosys Limited",
            sector="Technology & IT Services",
            ticker_nse="INFY",
            ticker_bse="INFY",
        )

    def test_company_instantiation(self) -> None:
        co = self._make_company()
        assert co.isin == "INE009A01021"
        assert co.ticker_nse == "INFY"

    def test_company_defaults(self) -> None:
        co = self._make_company()
        assert co.is_active is True
        assert co.aliases == []
        assert co.market_cap_cr is None

    def test_company_to_dict(self) -> None:
        co = self._make_company()
        d = co.to_dict()
        assert d["isin"] == "INE009A01021"
        assert d["sector"] == "Technology & IT Services"
        assert d["is_active"] is True

    def test_company_from_dict_roundtrip(self) -> None:
        from schemas.company import Company
        co = self._make_company()
        d = co.to_dict()
        restored = Company.from_dict(d)
        assert restored.isin == co.isin
        assert restored.company_name == co.company_name
        assert restored.sector == co.sector

    def test_market_cap_category_enum(self) -> None:
        from schemas.company import MarketCapCategory
        assert MarketCapCategory.LARGE_CAP.value == "large_cap"
        assert MarketCapCategory.UNKNOWN.value == "unknown"


class TestPriceRecordSchema:
    """Tests for schemas.market.PriceRecord"""

    def _make_price(self) -> object:
        from schemas.market import PriceRecord
        return PriceRecord(
            symbol="INFY",
            date=date(2024, 1, 15),
            open=1600.0,
            high=1625.0,
            low=1595.0,
            close=1615.0,
            adj_close=1615.0,
            volume=3_500_000,
        )

    def test_price_record_instantiation(self) -> None:
        pr = self._make_price()
        assert pr.symbol == "INFY"
        assert pr.close == 1615.0

    def test_price_record_daily_return_default(self) -> None:
        pr = self._make_price()
        assert pr.daily_return is None

    def test_price_record_to_dict(self) -> None:
        pr = self._make_price()
        d = pr.to_dict()
        assert d["symbol"] == "INFY"
        assert d["date"] == "2024-01-15"
        assert d["volume"] == 3_500_000

    def test_price_record_repr(self) -> None:
        pr = self._make_price()
        assert "INFY" in repr(pr)


class TestPredictionSchema:
    """Tests for schemas.prediction.Prediction"""

    def test_impact_label_enum(self) -> None:
        from schemas.prediction import ImpactLabel
        assert ImpactLabel.POSITIVE.value == "positive"
        assert ImpactLabel.NEGATIVE.value == "negative"
        assert ImpactLabel.NEUTRAL.value == "neutral"

    def test_prediction_instantiation(self) -> None:
        from schemas.prediction import ImpactLabel, Prediction
        pred = Prediction(
            bill_id="finance-bill-2024",
            model_version="v0.1.0",
            predicted_at=datetime(2024, 6, 1, 12, 0, 0),
            overall_impact=ImpactLabel.POSITIVE,
        )
        assert pred.bill_id == "finance-bill-2024"
        assert pred.overall_impact == ImpactLabel.POSITIVE
        assert pred.companies == []

    def test_prediction_to_dict(self) -> None:
        from schemas.prediction import ImpactLabel, Prediction
        pred = Prediction(
            bill_id="test-bill",
            model_version="v0.1",
            predicted_at=datetime(2024, 1, 1),
            overall_impact=ImpactLabel.NEUTRAL,
        )
        d = pred.to_dict()
        assert d["bill_id"] == "test-bill"
        assert d["overall_impact"] == "neutral"
        assert isinstance(d["companies"], list)
        assert isinstance(d["sectors"], list)

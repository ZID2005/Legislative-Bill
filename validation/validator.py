"""
validation/validator.py
=======================
Data validation module.

Validates all incoming data records before they are persisted or processed
downstream. Validation is the first gate in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from config.logging_config import get_logger
from schemas.bill import Bill, BillHouse, BillStatus

logger = get_logger(__name__)


@dataclass
class ValidationReport:
    """
    Accumulates errors and warnings discovered during data validation.

    Attributes
    ----------
    errors : list[str]
        List of critical failures that make the record invalid/unusable.
    warnings : list[str]
        List of non-blocking issues (e.g. missing optional fields).
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if there are zero validation errors."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add a critical validation error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a non-blocking validation warning."""
        self.warnings.append(message)

    def merge(self, other: ValidationReport) -> None:
        """Merge another validation report into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class Validator:
    """
    Data validation service for legislative bills, companies, and market data.
    """

    def validate_bill(self, bill: Any) -> ValidationReport:
        """
        Validate a Bill instance or a raw dictionary representing a bill.

        Parameters
        ----------
        bill : Bill or dict
            The bill record to validate.

        Returns
        -------
        ValidationReport
            The validation report containing errors and warnings.
        """
        report = ValidationReport()

        if isinstance(bill, dict):
            # Dict validation helper
            self._validate_bill_dict(bill, report)
        elif isinstance(bill, Bill):
            self._validate_bill_object(bill, report)
        else:
            report.add_error(
                f"Invalid bill input type: {type(bill).__name__}. Expected Bill object or dict."
            )

        if not report.is_valid:
            logger.error("Validation failed for bill. Errors: %s", report.errors)
        elif report.warnings:
            logger.warning(
                "Validation completed with warnings for bill. Warnings: %s", report.warnings
            )

        return report

    def _validate_bill_dict(self, data: dict[str, Any], report: ValidationReport) -> None:
        """Helper to validate raw bill dictionary."""
        # bill_id, title, url are hard required; year and ministry are now optional
        required_fields = ["bill_id", "title", "url"]
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                report.add_error(f"Missing required field: '{field_name}'")
            elif isinstance(data[field_name], str) and not data[field_name].strip():
                report.add_error(f"Required field '{field_name}' is empty")

        # Year validation — None is acceptable (warn); invalid range is an error
        year_val = data.get("year")
        if year_val is None:
            report.add_warning("Missing optional field: 'year'. Year could not be determined.")
        else:
            try:
                year_int = int(year_val)
                current_year = date.today().year
                if not (1947 <= year_int <= current_year + 1):
                    report.add_error(
                        f"Invalid year: {year_int}. Must be between 1947 and {current_year + 1}."
                    )
            except (ValueError, TypeError):
                report.add_error(f"Field 'year' must be an integer or None: {year_val}")

        # Ministry — empty is a warning, not an error (collected from detail page)
        if not data.get("ministry"):
            report.add_warning(
                "Missing optional field: 'ministry'. Will be populated from detail page."
            )

        # House validation
        if "house" in data and data["house"] is not None:
            house_val = data["house"]
            if house_val not in [h.value for h in BillHouse]:
                report.add_error(
                    f"Invalid house: '{house_val}'. Must be one of {[h.value for h in BillHouse]}"
                )

        # Status validation
        if "status" in data and data["status"] is not None:
            status_val = data["status"]
            if status_val not in [s.value for s in BillStatus]:
                report.add_error(
                    f"Invalid status: '{status_val}'. Must be one of {[s.value for s in BillStatus]}"
                )

        # URL validation
        if "url" in data and data["url"] is not None:
            url_val = str(data["url"])
            if not url_val.startswith("https://") and not url_val.startswith("http://"):
                report.add_error(f"Malformed URL: '{url_val}'. Must start with http:// or https://")

        # PDF URL validation — warning only if provided but malformed
        pdf_url_val = data.get("pdf_url")
        if pdf_url_val is not None:
            if not str(pdf_url_val).startswith("http://") and not str(pdf_url_val).startswith(
                "https://"
            ):
                report.add_warning(
                    f"Malformed pdf_url: '{pdf_url_val}'. Should start with http(s)://"
                )

        # Warnings for missing optional but recommended fields
        if not data.get("bill_number"):
            report.add_warning("Missing recommended field: 'bill_number'")
        if not data.get("pdf_path"):
            report.add_warning("Missing optional field: 'pdf_path'")
        if not data.get("full_text"):
            report.add_warning("Missing optional field: 'full_text'")

    def _validate_bill_object(self, bill: Bill, report: ValidationReport) -> None:
        """Helper to validate a Bill domain object."""
        # Check required identity fields
        if not bill.bill_id or not bill.bill_id.strip():
            report.add_error("Required field 'bill_id' is empty")
        if not bill.title or not bill.title.strip():
            report.add_error("Required field 'title' is empty")
        if not bill.url or not bill.url.strip():
            report.add_error("Required field 'url' is empty")
        else:
            if not bill.url.startswith("https://") and not bill.url.startswith("http://"):
                report.add_error(
                    f"Malformed URL: '{bill.url}'. Must start with http:// or https://"
                )

        # Year validation — None is acceptable (warning); invalid range is an error
        if bill.year is None:
            report.add_warning("Missing optional field: 'year'. Year could not be determined.")
        else:
            current_year = date.today().year
            if not (1947 <= bill.year <= current_year + 1):
                report.add_error(
                    f"Invalid year: {bill.year}. Must be between 1947 and {current_year + 1}."
                )

        # Ministry — empty is a warning not an error
        if not bill.ministry:
            report.add_warning(
                "Missing optional field: 'ministry'. Will be populated from detail page."
            )

        # Enums validation (since dataclass holds enum type, we verify types)
        if not isinstance(bill.house, BillHouse):
            report.add_error(
                f"Invalid house type: {type(bill.house).__name__}. Expected BillHouse Enum."
            )
        if not isinstance(bill.status, BillStatus):
            report.add_error(
                f"Invalid status type: {type(bill.status).__name__}. Expected BillStatus Enum."
            )

        # PDF URL validation — warning if provided but malformed
        if bill.pdf_url is not None:
            if not bill.pdf_url.startswith("http://") and not bill.pdf_url.startswith("https://"):
                report.add_warning(
                    f"Malformed pdf_url: '{bill.pdf_url}'. Should start with http(s)://"
                )

        # Date fields type checks
        for date_field_name in [
            "introduction_date",
            "assent_date",
            "gazette_date",
            "last_updated",
            "ingested_at",
        ]:
            val = getattr(bill, date_field_name)
            if val is not None and not isinstance(val, date):
                report.add_error(
                    f"Field '{date_field_name}' must be a datetime.date object. Got {type(val).__name__}."
                )

        # Warnings
        if not bill.bill_number:
            report.add_warning("Missing recommended field: 'bill_number'")
        if not bill.pdf_path:
            report.add_warning("Missing optional field: 'pdf_path'")
        if not bill.full_text:
            report.add_warning("Missing optional field: 'full_text'")

    def validate_knowledge_record(self, record: Any) -> ValidationReport:
        """
        Validate a KnowledgeRecord instance for semantic correctness.
        Detects unknown ministries, unknown policy domains, missing mappings,
        conflicting mappings, and duplicate keywords.
        """
        from schemas.knowledge_record import KnowledgeRecord
        from knowledge.loader import list_ministries, list_sectors, get_ministry_sectors
        import csv
        from pathlib import Path

        report = ValidationReport()

        if not isinstance(record, KnowledgeRecord):
            report.add_error(
                f"Invalid input type: {type(record).__name__}. Expected KnowledgeRecord object."
            )
            return report

        # Load lookup tables for validation
        known_ministries = list_ministries()
        known_sectors = list_sectors()

        # Load sector domain mapping to get known policy domains
        known_policy_domains = set()
        sector_domain_file = (
            Path(__file__).resolve().parent.parent / "knowledge" / "sector_domain_mapping.csv"
        )
        if sector_domain_file.is_file():
            with open(sector_domain_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pd = row.get("policy_domain", "").strip()
                    if pd:
                        known_policy_domains.add(pd.lower())

        # Load departments to check for department mappings
        known_departments_ministries = set()
        departments_file = Path(__file__).resolve().parent.parent / "knowledge" / "departments.csv"
        if departments_file.is_file():
            with open(departments_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    m = row.get("ministry", "").strip().lower()
                    if m:
                        known_departments_ministries.add(m)

        # 1. Detect Unknown Ministries
        if record.ministry not in known_ministries:
            report.add_error(f"Unknown ministry: '{record.ministry}'")

        # 2. Detect Unknown Policy Domains
        if (
            record.policy_domain.lower() not in known_policy_domains
            and record.policy_domain != "Unknown Policy Domain"
        ):
            report.add_error(f"Unknown policy domain: '{record.policy_domain}'")

        # 3. Detect Missing Mappings
        # Sponsoring ministry has no mapped primary sector in ministry_sector.csv
        if record.ministry in known_ministries:
            min_sectors = get_ministry_sectors(record.ministry)
            if not min_sectors:
                report.add_warning(
                    f"Missing mapping: Sponsoring ministry '{record.ministry}' has no sectors mapped in ministry_sector.csv"
                )

        # Sponsoring ministry has no department mapping
        if record.ministry.lower() not in known_departments_ministries:
            report.add_warning(
                f"Missing mapping: Sponsoring ministry '{record.ministry}' has no department mapped in departments.csv"
            )

        if record.policy_domain == "Unknown Policy Domain":
            report.add_warning(
                f"Missing mapping: Sector '{record.primary_sector}' has no policy domain mapping"
            )
        if record.economic_domain == "Unknown Economic Domain":
            report.add_warning(
                f"Missing mapping: Sector '{record.primary_sector}' has no economic domain mapping"
            )

        # 4. Detect Conflicting Mappings
        if record.ministry in known_ministries and record.primary_sector in known_sectors:
            regulated_sectors = get_ministry_sectors(record.ministry)
            if regulated_sectors and "All Sectors" not in regulated_sectors:
                if (
                    record.primary_sector not in regulated_sectors
                    and "All Sectors" not in record.primary_sector
                ):
                    report.add_error(
                        f"Conflicting mapping: Ministry '{record.ministry}' regulates {regulated_sectors}, "
                        f"but primary sector is '{record.primary_sector}'"
                    )

        # 5. Detect Duplicate Keywords
        if record.keywords:
            seen = set()
            duplicates = []
            for kw in record.keywords:
                kw_lower = kw.lower().strip()
                if kw_lower in seen:
                    duplicates.append(kw)
                else:
                    seen.add(kw_lower)
            if duplicates:
                report.add_warning(f"Duplicate keywords detected: {list(set(duplicates))}")

        if not report.is_valid:
            logger.error("Validation failed for KnowledgeRecord. Errors: %s", report.errors)
        elif report.warnings:
            logger.warning(
                "Validation completed with warnings for KnowledgeRecord. Warnings: %s",
                report.warnings,
            )

        return report

    def validate_company(self, record: Any) -> ValidationReport:
        """
        Validate a Company instance or raw dictionary for correctness.
        Detects missing company names, missing sectors, invalid websites,
        and invalid states.
        """
        from schemas.company import Company

        report = ValidationReport()

        is_dict = isinstance(record, dict)
        if not is_dict and not isinstance(record, Company):
            report.add_error(
                f"Invalid company input type: {type(record).__name__}. Expected Company object or dict."
            )
            return report

        # Extract fields based on type
        isin = record.get("isin", "") if is_dict else getattr(record, "isin", "")
        name = record.get("company_name", "") if is_dict else getattr(record, "company_name", "")
        sector = record.get("sector", "") if is_dict else getattr(record, "sector", "")
        website = record.get("website", "") if is_dict else getattr(record, "website", "")
        state = record.get("hq_state", "") if is_dict else getattr(record, "hq_state", "")

        # 1. Missing Company Name
        if not name or not str(name).strip():
            report.add_error("Missing company name")

        # 2. Missing ISIN
        if not isin or not str(isin).strip():
            report.add_error("Missing ISIN")

        # 3. Missing Sector
        if not sector or str(sector).strip() == "" or str(sector).strip() == "Unknown Sector":
            report.add_warning("Missing sector")

        # 4. Invalid Websites
        if website and str(website).strip():
            web_str = str(website).strip()
            if not web_str.startswith("http://") and not web_str.startswith("https://"):
                report.add_error(
                    f"Invalid website: '{web_str}'. Must start with http:// or https://"
                )

        # 5. Invalid States
        VALID_STATES = {
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chhattisgarh",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jharkhand",
            "Karnataka",
            "Kerala",
            "Madhya Pradesh",
            "Maharashtra",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Odisha",
            "Punjab",
            "Rajasthan",
            "Sikkim",
            "Tamil Nadu",
            "Telangana",
            "Tripura",
            "Uttar Pradesh",
            "Uttarakhand",
            "West Bengal",
            "Delhi",
            "Jammu and Kashmir",
            "Puducherry",
            "Ladakh",
            "Chandigarh",
            "Lakshadweep",
            "Dadra and Nagar Haveli and Daman and Diu",
            "Andaman and Nicobar Islands",
        }
        if state and str(state).strip():
            state_str = str(state).strip()
            if state_str not in VALID_STATES:
                report.add_error(
                    f"Invalid state: '{state_str}'. Must be a valid Indian state or UT."
                )

        return report

    def validate_companies_list(self, companies: list[Any]) -> ValidationReport:
        """
        Validate a collection of company records for correctness.
        Specifically detects duplicate NSE symbols and duplicate ISINs.
        """
        from schemas.company import Company

        report = ValidationReport()

        seen_symbols = {}
        seen_isins = {}

        for idx, record in enumerate(companies):
            # Validate individual record first
            record_report = self.validate_company(record)
            report.merge(record_report)

            is_dict = isinstance(record, dict)
            isin = record.get("isin", "") if is_dict else getattr(record, "isin", "")
            symbol = record.get("ticker_nse", "") if is_dict else getattr(record, "ticker_nse", "")

            # Detect Duplicate ISINs
            if isin:
                isin_upper = str(isin).strip().upper()
                if isin_upper in seen_isins:
                    report.add_error(
                        f"Duplicate ISIN detected: '{isin_upper}' (at indices {seen_isins[isin_upper]} and {idx})"
                    )
                else:
                    seen_isins[isin_upper] = idx

            # Detect Duplicate NSE symbols
            if symbol:
                sym_upper = str(symbol).strip().upper()
                if sym_upper in seen_symbols:
                    report.add_error(
                        f"Duplicate NSE symbol detected: '{sym_upper}' (at indices {seen_symbols[sym_upper]} and {idx})"
                    )
                else:
                    seen_symbols[sym_upper] = idx

        return report

    def validate_market_df(self, df: Any) -> ValidationReport:
        """Validate a market price DataFrame."""
        import pandas as pd  # noqa: PLC0415

        report = ValidationReport()
        if df is None:
            report.add_error("DataFrame is None")
            return report

        if not isinstance(df, pd.DataFrame):
            report.add_error(f"Input is not a pandas DataFrame: type={type(df)}")
            return report

        if df.empty:
            report.add_warning("DataFrame is empty")
            return report

        # 1. Missing OHLC fields
        required_cols = ["Date", "Open", "High", "Low", "Close", "Adjusted Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                report.add_error(f"Missing required column: '{col}'")

        if not report.is_valid:
            return report

        # 2. Duplicate rows (duplicate dates)
        duplicate_dates = df[df.duplicated(subset=["Date"], keep=False)]["Date"].unique()
        for d in duplicate_dates:
            report.add_error(f"Duplicate row for date: '{d}'")

        # 3. Numeric checks, invalid prices, negative prices
        for idx, row in df.iterrows():
            d = row["Date"]

            # Check date format
            try:
                pd.to_datetime(d)
            except Exception:
                report.add_error(f"Row {idx}: Invalid date value: '{d}'")

            # Check prices
            for col in ["Open", "High", "Low", "Close", "Adjusted Close"]:
                val = row[col]
                if pd.isna(val):
                    report.add_error(f"Row {idx} ({d}): Missing value in column '{col}'")
                else:
                    try:
                        f_val = float(val)
                        if f_val <= 0:
                            report.add_error(
                                f"Row {idx} ({d}): Negative or zero price in column '{col}': {f_val}"
                            )
                    except (ValueError, TypeError):
                        report.add_error(
                            f"Row {idx} ({d}): Non-numeric value in column '{col}': {val}"
                        )

            # Check Volume
            vol = row["Volume"]
            if pd.isna(vol):
                report.add_error(f"Row {idx} ({d}): Missing value in column 'Volume'")
            else:
                try:
                    f_vol = float(vol)
                    if f_vol < 0:
                        report.add_error(
                            f"Row {idx} ({d}): Negative volume in column 'Volume': {f_vol}"
                        )
                except (ValueError, TypeError):
                    report.add_error(
                        f"Row {idx} ({d}): Non-numeric value in column 'Volume': {vol}"
                    )

        # 4. Check for missing trading days (gaps)
        try:
            dates = pd.to_datetime(df["Date"]).sort_values()
            diffs = dates.diff()
            for i in range(1, len(dates)):
                d_diff = diffs.iloc[i].days
                if d_diff > 5:
                    prev_date = dates.iloc[i - 1].strftime("%Y-%m-%d")
                    curr_date = dates.iloc[i].strftime("%Y-%m-%d")
                    report.add_warning(
                        f"Potential gap in trading days detected between {prev_date} and {curr_date} ({d_diff} days gap)"
                    )
        except Exception as e:
            report.add_warning(f"Could not verify trading day gaps: {e}")

        return report

    def validate_document(
        self, pdf_path: Path, expected_mime: str = "application/pdf", min_size_bytes: int = 100
    ) -> ValidationReport:
        """
        Validate the downloaded PDF document.
        Checks for file extension, file size, PDF magic signature,
        and PyPDF2 parsing errors.
        """
        report = ValidationReport()
        if not pdf_path.is_file():
            report.add_error(f"File does not exist: {pdf_path}")
            return report

        # Extension Check
        if pdf_path.suffix.lower() != ".pdf":
            report.add_error(f"Invalid file extension: '{pdf_path.suffix}'. Expected '.pdf'")

        # Size Check
        size = pdf_path.stat().st_size
        if size < min_size_bytes:
            report.add_error(
                f"File size too small: {size} bytes. Minimum expected: {min_size_bytes} bytes."
            )

        # Signature & Corruption Check
        try:
            with pdf_path.open("rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    report.add_error("Invalid PDF signature. File does not start with %PDF")

                # Additional structural check via PyPDF2
                import PyPDF2  # noqa: PLC0415

                f.seek(0)
                reader = PyPDF2.PdfReader(f)
                # Access pages to parse cross-reference table and trailer.
                # If the file is truncated/corrupted, this will raise.
                _ = len(reader.pages)
        except Exception as e:
            report.add_error(f"Corrupted PDF file structure: {e}")

        return report

    def _sectors_match(self, s1: str, s2: str) -> bool:
        """Check if two sector names match (case-insensitive, allows substring matching for longer names)."""
        clean1 = s1.strip().lower()
        clean2 = s2.strip().lower()
        if clean1 == clean2:
            return True
        if len(clean1) > 4 and clean1 in clean2:
            return True
        if len(clean2) > 4 and clean2 in clean1:
            return True
        return False

    def validate_mapping_record(self, record: Any, company_repo: Any) -> ValidationReport:
        """
        Validate a BillCompanyMapping record for semantic correctness.
        Detects unknown sectors, duplicate candidate companies, missing companies,
        and conflicting mappings.
        """
        from schemas.mapping_record import BillCompanyMapping
        from knowledge.loader import list_sectors, list_ministries, get_ministry_sectors
        import csv
        from pathlib import Path

        report = ValidationReport()

        if isinstance(record, dict):
            try:
                record = BillCompanyMapping.from_dict(record)
            except Exception as e:
                report.add_error(f"Failed to parse mapping record from dict: {e}")
                return report

        if not isinstance(record, BillCompanyMapping):
            report.add_error(
                f"Invalid input type: {type(record).__name__}. Expected BillCompanyMapping object."
            )
            return report

        # Load lookup tables for validation
        known_sectors = list_sectors()
        for m in list_ministries():
            for s in get_ministry_sectors(m):
                if s:
                    known_sectors.append(s)

        sector_domain_file = (
            Path(__file__).resolve().parent.parent / "knowledge" / "sector_domain_mapping.csv"
        )
        if sector_domain_file.is_file():
            with open(sector_domain_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sec = row.get("sector", "").strip()
                    if sec:
                        known_sectors.append(sec)

        try:
            for comp in company_repo.get_all():
                if comp.sector:
                    known_sectors.append(comp.sector)
        except Exception:
            pass

        known_sectors.extend(
            [
                "trade",
                "chemicals",
                "aviation",
                "ports & shipping",
                "railways",
                "governance & public administration",
            ]
        )
        known_sectors_lower = {s.lower() for s in known_sectors if s}

        # 1. Detect Unknown Sectors
        if record.primary_sector and record.primary_sector.lower() not in known_sectors_lower:
            report.add_error(f"Unknown primary sector: '{record.primary_sector}'")

        for sec in record.secondary_sectors:
            if sec and sec.lower() not in known_sectors_lower:
                report.add_error(f"Unknown secondary sector: '{sec}'")

        # 2. Detect Companies Mapped Twice (Duplicate ISINs)
        seen_isins = set()
        duplicates = []
        for comp in record.candidate_companies:
            isin = comp.get("isin", "").strip().upper()
            if isin:
                if isin in seen_isins:
                    duplicates.append(isin)
                else:
                    seen_isins.add(isin)
        if duplicates:
            report.add_error(f"Companies mapped twice (duplicate ISINs): {list(set(duplicates))}")

        # 3. Detect Missing Companies
        # Warning if candidate list is empty, but there are active companies in database
        # that match primary_sector or secondary_sectors.
        if not record.candidate_companies:
            sectors_to_check = []
            if record.primary_sector:
                sectors_to_check.append(record.primary_sector.lower())
            for sec in record.secondary_sectors:
                if sec:
                    sectors_to_check.append(sec.lower())

            # Load overrides and check active companies
            company_overrides = {}
            company_sector_file = (
                Path(__file__).resolve().parent.parent / "knowledge" / "company_sector.csv"
            )
            if company_sector_file.is_file():
                with open(company_sector_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        isin = row.get("isin", "").strip().upper()
                        override_sector = row.get("override_sector", "").strip()
                        if isin and override_sector:
                            company_overrides[isin] = override_sector.lower()

            all_companies = company_repo.get_all()
            companies_in_sectors = []
            for comp in all_companies:
                if not comp.is_active:
                    continue
                comp_isin = comp.isin.strip().upper()
                comp_sector = company_overrides.get(comp_isin, comp.sector).strip().lower()
                if comp_sector in sectors_to_check:
                    companies_in_sectors.append(comp)

            if companies_in_sectors:
                matching_tickers = [c.ticker_nse for c in companies_in_sectors if c.ticker_nse]
                report.add_warning(
                    f"Missing companies: candidate list is empty, but active companies {matching_tickers} "
                    f"exist in the database matching sectors {sectors_to_check}."
                )

        # 4. Detect Conflicting Mappings
        # Read ministry sectors mapping
        ministry_sectors = {}
        ministry_sector_file = (
            Path(__file__).resolve().parent.parent / "knowledge" / "ministry_sector.csv"
        )
        if ministry_sector_file.is_file():
            with open(ministry_sector_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    m = row.get("ministry", "").strip().lower()
                    if m:
                        primary = row.get("primary_sector", "").strip()
                        sec_raw = row.get("secondary_sectors", "").strip()
                        sec_list = []
                        if sec_raw:
                            clean_sec = sec_raw.strip('"').strip("'")
                            sec_list = [s.strip() for s in clean_sec.split(",") if s.strip()]

                        all_sectors = []
                        if primary:
                            all_sectors.append(primary.lower())
                        for s in sec_list:
                            all_sectors.append(s.lower())
                        ministry_sectors[m] = all_sectors

        # Get allowed sectors for this bill (primary + secondary)
        allowed_sectors_lower = {
            s.lower() for s in ([record.primary_sector] + record.secondary_sectors) if s
        }

        for comp in record.candidate_companies:
            comp_name = comp.get("company_name", "")
            comp_sector = comp.get("sector", "")

            # Check if mapped company's sector is actually in the bill's primary/secondary sectors
            if not any(
                self._sectors_match(comp_sector, allowed_sec)
                for allowed_sec in allowed_sectors_lower
            ):
                report.add_error(
                    f"Conflicting mapping: Company '{comp_name}' in sector '{comp_sector}' "
                    f"is mapped to bill with sectors {list(allowed_sectors_lower)}"
                )

            # Check if company's sector conflicts with bill's sponsoring ministry
            if record.ministry:
                m_lower = record.ministry.strip().lower()
                if m_lower in ministry_sectors:
                    m_sectors = ministry_sectors[m_lower]
                    if m_sectors and "all sectors" not in m_sectors:
                        if not any(self._sectors_match(comp_sector, m_sec) for m_sec in m_sectors):
                            report.add_warning(
                                f"Conflicting mapping: Company '{comp_name}' in sector '{comp_sector}' "
                                f"is mapped to a bill sponsored by ministry '{record.ministry}' which only regulates {m_sectors}"
                            )

        if not report.is_valid:
            logger.error("Validation failed for BillCompanyMapping. Errors: %s", report.errors)
        elif report.warnings:
            logger.warning(
                "Validation completed with warnings for BillCompanyMapping. Warnings: %s",
                report.warnings,
            )

        return report

    def validate_mappings_list(self, records: list[Any], company_repo: Any) -> ValidationReport:
        """
        Validate a collection of mapping records.
        """
        report = ValidationReport()
        for idx, rec in enumerate(records):
            rec_report = self.validate_mapping_record(rec, company_repo)
            report.merge(rec_report)
        return report

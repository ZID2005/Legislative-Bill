"""
knowledge package
=================
Curated, human-editable knowledge base for the Legislative Intelligence project.

This package contains **domain knowledge that is not learned by the model** —
it is explicitly curated by domain experts and provides the ground-truth
mappings that the NLP and mapping modules rely on.

Why a separate knowledge package?
----------------------------------
ML models are good at pattern recognition but bad at authoritative domain
facts.  For example, the model should not "learn" that the Finance Ministry
is responsible for banking regulation — that is a fact that must be
explicitly encoded and kept up to date.

Contents
--------
Data files (CSV):

    ministry_sector.csv     : Maps Government of India ministries to the
                              economic sectors they regulate.

    sector_keywords.csv     : Curated keyword lists per sector.  Used in the
                              Phase A (keyword-based) sector mapper.

    policy_keywords.csv     : Keywords indicating specific policy intent
                              (e.g. "tax exemption", "import duty",
                              "FDI limit", "licensing requirement").

    bill_categories.csv     : Maps known bill types to their primary sector.
                              E.g. Finance Bill → Banking, Capital Markets.

    company_sector.csv      : Override mapping: ISIN → sector.
                              For companies that cross-list in multiple
                              sectors or where the exchange classification
                              is incorrect.

Python loader:

    loader.py               : Functions to read knowledge files into
                              in-memory structures for use by mappers.

Usage
-----
    from knowledge.loader import (
        get_ministry_sectors,
        get_sector_keywords,
        get_policy_keywords,
    )

    sectors = get_ministry_sectors("Ministry of Finance")
    keywords = get_sector_keywords("Banking")

Maintenance
-----------
These CSV files should be reviewed and updated:
*  When new bills are ingested from previously uncovered sectors
*  When Government ministries are reorganised
*  When the NSE/BSE sector taxonomy changes

DO NOT auto-generate these files from ML outputs.  They must remain
human-curated to serve as reliable ground truth.
"""

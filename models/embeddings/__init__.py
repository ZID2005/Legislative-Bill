"""
models/embeddings package
==========================
Text embedding generation for bill and sector descriptions.

Responsibility
--------------
Convert raw text into dense numerical representations that capture semantic
meaning — essential for the NLP-based sector mapping (Task 5) and the
feature engineering pipeline (Task 7).

Planned modules
---------------
bill_embedder.py
    Generate fixed-length embeddings for bill clauses and summaries.
    Primary model: Legal-RoBERTa or Sentence-BERT.

sector_embedder.py
    Generate embeddings for sector descriptions (from knowledge/sector_keywords.csv).
    Used for cosine-similarity-based bill → sector mapping.

embedding_cache.py
    Disk-backed embedding cache so large bills are not re-embedded on every run.

Implemented in Task 7.
"""

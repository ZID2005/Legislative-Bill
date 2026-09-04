"""
models package
==============
Machine learning model layer for the Legislative Intelligence project.

This package is responsible for all model-related code: embedding generation,
training, inference, and evaluation.  It is divided into sub-packages to
keep concerns separated as the ML complexity grows.

Sub-packages
------------
embeddings/  : Text embedding generation (FinBERT, Legal-RoBERTa).
               Converts bill text into dense vector representations.
               Implemented in Task 7 (alongside feature engineering).

training/    : Model training pipeline (Task 6.1).
               Implements:
               * DatasetBuilder  -- leakage-free training/research split
               * MLTrainer       -- trains 4 targets x 3 algorithms
               * Chronological TimeSeriesSplit validation
               * GridSearchCV hyperparameter selection
               * ModelRepository integration

prediction/  : Inference engine.
               Loads trained artefacts and produces ``Prediction`` schema
               objects for new bills.
               Implemented in Task 9.

evaluation/  : Model evaluation and backtesting.
               Computes metrics (AUROC, F1, MAE, RMSE) and generates
               evaluation reports.
               Implemented in Task 8 (alongside training).

Artefacts
---------
Trained model files are stored under ``models/<target>/<model_type>/``.
Each artefact set includes:
*  ``model.pkl``            -- the trained estimator bundle (joblib-serialised)
*  ``preprocessor.pkl``     -- the fitted ColumnTransformer
*  ``features.json``        -- ordered feature column list
*  ``metadata.json``        -- training metadata
*  ``training_report.json`` -- complete training metrics report

Datasets
--------
ML-ready datasets are stored under ``data/ml/``:
*  ``training_dataset.parquet`` -- leakage-free (pre-event features + labels)
*  ``research_dataset.parquet`` -- full feature set (for academic analysis only)
"""

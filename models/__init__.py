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

training/    : Model training pipeline.
               Implements LightGBM training, Optuna hyperparameter search,
               and MLflow experiment tracking.
               Implemented in Task 8.

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
Trained model files are stored under ``models/artefacts/`` (git-ignored).
Each artefact set includes:
*  ``<name>_<date>.pkl`` — the trained model (joblib-serialised)
*  ``<name>_<date>_schema.json`` — the FeatureSchema used at training time
*  ``<name>_<date>_metrics.json`` — evaluation metrics on the held-out test set
"""

"""
models/evaluation package
==========================
Model evaluation and backtesting.

Responsibility
--------------
Assess model performance on held-out data and generate structured
evaluation reports.

Planned modules
---------------
metrics.py
    Compute classification metrics (AUROC, F1-macro, Cohen's Kappa)
    and regression metrics (MAE, RMSE, Pearson ρ).

backtester.py
    Simulate a trading strategy driven by model predictions.
    Measures Sharpe ratio, maximum drawdown, and information ratio.

report_generator.py
    Produce a structured HTML/PDF evaluation report per model version,
    including metric tables, calibration curves, and SHAP summary plots.

Implemented in Task 8.
"""

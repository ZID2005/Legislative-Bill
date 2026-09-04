"""
backtesting package
===================
Historical Backtesting Engine layer for Task 6.4 / 6.4.1.

Modules
-------
- `engine`: Master orchestrator for walk-forward backtesting.
- `strategy`: Signal construction, PortfolioAccountant, and transaction cost modeling.
- `metrics`: Classification and financial performance metrics calculations.
- `visualizer`: Matplotlib chart generators.
- `report_generator`: JSON/Parquet report builder.
- `nifty_loader`: Real NIFTY 50 benchmark period returns loader.
- `overlap_detector`: Event-window overlap analysis.
- `financial_validator`: Post-hoc financial integrity checks.
"""

from backtesting.engine import HistoricalBacktestEngine
from backtesting.strategy import SignalRule, TransactionCostModel, StrategyEvaluator, PortfolioAccountant
from backtesting.metrics import ClassificationMetricsCalculator, FinancialMetricsCalculator
from backtesting.visualizer import BacktestVisualizer
from backtesting.report_generator import BacktestReportGenerator
from backtesting.nifty_loader import NiftyBenchmarkLoader
from backtesting.overlap_detector import OverlapDetector
from backtesting.financial_validator import FinancialValidator

__all__ = [
    "HistoricalBacktestEngine",
    "SignalRule",
    "TransactionCostModel",
    "StrategyEvaluator",
    "PortfolioAccountant",
    "ClassificationMetricsCalculator",
    "FinancialMetricsCalculator",
    "BacktestVisualizer",
    "BacktestReportGenerator",
    "NiftyBenchmarkLoader",
    "OverlapDetector",
    "FinancialValidator",
]

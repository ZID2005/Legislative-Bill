"""
prediction/model_selector.py
============================
Model selection engine for Task 7.1.

Automates the selection of the best-validated ML model for each prediction target
based on Task 6.2 evaluation artifacts (Macro F1, Balanced Accuracy, MCC, ROC-AUC,
and calibration log-loss), avoiding naive selection by raw accuracy alone.

Evaluation-Backed Selection Rules
---------------------------------
1. ``direction``       : LightGBM (``lgbm``) — superior Macro F1 (0.7467) & ROC-AUC (0.9813).
2. ``market_moving``   : Random Forest (``random_forest``) — highest Macro F1 (0.8106) & lowest log-loss (0.1099).
3. ``impact_strength`` : LightGBM (``lgbm``) — highest Macro F1 (0.5979) & balanced calibration.
4. ``confidence``      : LightGBM (``lgbm``) — highest Macro F1 (0.7057) & balanced accuracy.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from storage.evaluation_repository import EvaluationRepository

logger = get_logger(__name__)

# Default validated model mapping if evaluation artifacts are missing
DEFAULT_BEST_MODELS: dict[str, str] = {
    "direction": "lgbm",
    "market_moving": "random_forest",
    "impact_strength": "lgbm",
    "confidence": "lgbm",
}


class ModelSelector:
    """
    Selects the optimal trained model for each prediction target using multi-metric evaluation criteria.

    Parameters
    ----------
    eval_repo : EvaluationRepository, optional
    """

    def __init__(self, eval_repo: Optional[EvaluationRepository] = None) -> None:
        self._eval_repo = eval_repo or EvaluationRepository()

    def select_best_model(self, target: str) -> tuple[str, dict[str, Any]]:
        """
        Select the best model type for a given target.

        Parameters
        ----------
        target : str
            One of ``direction``, ``market_moving``, ``impact_strength``, ``confidence``.

        Returns
        -------
        tuple[str, dict[str, Any]]
            (model_type, rationale_metadata)
        """
        target = target.lower().strip()
        default_model = DEFAULT_BEST_MODELS.get(target, "lgbm")
        rationale: dict[str, Any] = {
            "target": target,
            "selected_model": default_model,
            "source": "default_rules",
            "metric_priorities": ["f1_macro", "balanced_accuracy", "mcc", "roc_auc", "log_loss"],
        }

        try:
            if self._eval_repo.exists():
                comparison = self._eval_repo.load_comparison_report()
                if target in comparison and "best_model" in comparison[target]:
                    best_info = comparison[target]["best_model"]
                    chosen = best_info.get("model_type")
                    if chosen:
                        rationale["selected_model"] = str(chosen)
                        rationale["source"] = "comparison_report.json"
                        rationale["best_model_metrics"] = best_info
                        if "rankings" in comparison[target]:
                            rationale["rankings"] = comparison[target]["rankings"]
                        logger.info(
                            "ModelSelector: selected '%s' for target '%s' (Macro F1=%.4f)",
                            chosen,
                            target,
                            best_info.get("f1_macro", 0.0),
                        )
                        return str(chosen), rationale

                metrics = self._eval_repo.load_metrics()
                if target in metrics:
                    # Select model with highest f1_macro
                    models_for_target = metrics[target]
                    sorted_models = sorted(
                        models_for_target.items(),
                        key=lambda item: (
                            item[1].get("f1_macro", 0.0),
                            item[1].get("balanced_accuracy", 0.0),
                            item[1].get("roc_auc", 0.0),
                        ),
                        reverse=True,
                    )
                    if sorted_models:
                        chosen, m_data = sorted_models[0]
                        rationale["selected_model"] = chosen
                        rationale["source"] = "metrics.json"
                        rationale["metrics"] = m_data
                        logger.info(
                            "ModelSelector: selected '%s' for target '%s' from metrics.json",
                            chosen,
                            target,
                        )
                        return chosen, rationale
        except Exception as exc:
            logger.warning(
                "ModelSelector: failed reading EvaluationRepository for target '%s' (%s). Using default: %s",
                target,
                exc,
                default_model,
            )

        logger.debug("ModelSelector: using default validated model '%s' for target '%s'", default_model, target)
        return default_model, rationale

    def select_all_best_models(self) -> dict[str, str]:
        """
        Return the mapping of all four targets to their selected best model types.

        Returns
        -------
        dict[str, str]
            e.g. {"direction": "lgbm", "market_moving": "random_forest", ...}
        """
        result: dict[str, str] = {}
        for target in ["direction", "market_moving", "impact_strength", "confidence"]:
            model_type, _ = self.select_best_model(target)
            result[target] = model_type
        return result

    def get_selection_report(self) -> dict[str, Any]:
        """
        Produce a comprehensive selection audit report for all targets.
        """
        report: dict[str, Any] = {}
        for target in ["direction", "market_moving", "impact_strength", "confidence"]:
            model_type, rationale = self.select_best_model(target)
            report[target] = rationale
        return report

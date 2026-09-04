"""
models/evaluation/metrics.py
=============================
Classification metrics helper functions for Task 6.2.

Provides a unified interface to compute standard and advanced metrics:
- Accuracy, Balanced Accuracy, Matthews Correlation Coefficient (MCC)
- Precision (macro, weighted)
- Recall (macro, weighted)
- F1-score (macro, weighted)
- ROC-AUC (binary and multi-class)
- Log Loss (where probabilities are available)
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np
from config.logging_config import get_logger

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = get_logger(__name__)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    classes: Optional[Sequence[Any]] = None,
) -> dict[str, Any]:
    """
    Compute a dictionary of standard and advanced classification metrics.

    Parameters
    ----------
    y_true : np.ndarray
        Ground truth integer encoded targets.
    y_pred : np.ndarray
        Predicted integer encoded targets.
    y_prob : np.ndarray, optional
        Predicted class probabilities (shape: [n_samples, n_classes]).
    classes : list of Any, optional
        Sequence of class labels corresponding to class indices.

    Returns
    -------
    dict
        Dictionary containing all computed metrics.
    """
    results: dict[str, Any] = {}

    # Basic stats
    results["samples"] = int(len(y_true))

    # Standard metrics
    results["accuracy"] = float(accuracy_score(y_true, y_pred))
    results["balanced_accuracy"] = float(balanced_accuracy_score(y_true, y_pred))
    results["mcc"] = float(matthews_corrcoef(y_true, y_pred))

    # Precision / Recall / F1 (Macro)
    results["precision_macro"] = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    results["recall_macro"] = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    results["f1_macro"] = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    # Precision / Recall / F1 (Weighted)
    results["precision_weighted"] = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    results["recall_weighted"] = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    results["f1_weighted"] = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # Log Loss & ROC-AUC (where probabilities are available)
    results["log_loss"] = None
    results["roc_auc"] = None

    if y_prob is not None:
        n_classes = len(classes) if classes is not None else len(np.unique(y_true))

        # Check if shape of probabilities matches class counts
        if len(y_prob.shape) == 2 and y_prob.shape[1] == n_classes:
            # 1. Log Loss
            try:
                # Filter out classes that aren't present in y_true if log_loss errors
                results["log_loss"] = float(log_loss(y_true, y_prob, labels=np.arange(n_classes)))
            except Exception as exc:
                logger.debug("Failed to compute log loss: %s", exc)

            # 2. ROC-AUC
            try:
                if n_classes == 2:
                    # For binary target, pass probabilities of positive class (index 1)
                    # Handle cases where all targets belong to one class to prevent crash
                    if len(np.unique(y_true)) > 1:
                        results["roc_auc"] = float(roc_auc_score(y_true, y_prob[:, 1]))
                else:
                    # For multi-class target
                    if len(np.unique(y_true)) > 1:
                        results["roc_auc"] = float(
                            roc_auc_score(
                                y_true,
                                y_prob,
                                multi_class="ovr",
                                average="macro",
                                labels=np.arange(n_classes),
                            )
                        )
            except Exception as exc:
                logger.debug("Failed to compute ROC-AUC: %s", exc)
        else:
            logger.debug(
                "Skipping probability metrics: shape %s does not match class count %d",
                y_prob.shape,
                n_classes,
            )

    return results

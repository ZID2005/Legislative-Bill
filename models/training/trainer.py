"""
models/trainer.py
=================
Model training pipeline — **Task 8 placeholder**.

Future Responsibility
---------------------
This module will orchestrate the end-to-end training pipeline, from loading
the feature matrix to serialising the final model artefact.

Planned pipeline:

1.  **Data loading**
    Load the labelled feature matrix produced by ``feature_builder`` and
    ``label_generator``.

2.  **Train / validation / test split**
    Use a time-based split to prevent data leakage (bills from earlier
    years form the training set; recent bills form the test set).

3.  **Baseline models**
    *  Logistic Regression (classification)
    *  Linear Regression (regression / CAR prediction)
    *  Random Forest

4.  **Primary model: LightGBM**
    *  Gradient-boosted trees are well-suited to tabular features.
    *  Hyperparameter tuning via Optuna.

5.  **Optional advanced model: Transformer fine-tuning**
    *  Fine-tune FinBERT or Legal-RoBERTa on the bill classification task.
    *  Used as a text-only baseline or ensembled with LightGBM.

6.  **Evaluation metrics**
    *  Classification : Accuracy, F1-macro, AUROC, Cohen's Kappa
    *  Regression     : MAE, RMSE, Pearson ρ

7.  **Model serialisation**
    Save trained models as ``models/artefacts/<model_name>_<date>.pkl``
    using ``joblib``.  Also save the ``FeatureSchema`` alongside the model
    to prevent inference-time skew.

8.  **Experiment tracking**
    Log all runs (hyperparameters, metrics, artefact paths) to MLflow.

Dependencies (to be added in Task 8)
--------------------------------------
*  scikit-learn
*  lightgbm
*  optuna
*  mlflow
*  joblib
"""

# TODO (Task 8): Implement Trainer class and train() entry point.


class Trainer:
    """
    Placeholder for the model training pipeline.

    Full implementation planned for Task 8.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "Trainer is not yet implemented.  See Task 8."
        )

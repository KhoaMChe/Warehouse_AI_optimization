import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
)


def train_model(
    feature: pd.DataFrame,
    target: str,
    drop_cols: list,
    model,
):
    """
    Train một model phân loại.

    Parameters
    ----------
    feature : DataFrame
    target : cột cần dự đoán
    drop_cols : các cột loại bỏ
    model : sklearn model

    Returns
    -------
    model
    feature_columns
    importance
    """

    feature = feature.copy()

    # --------------------------
    # Target
    # --------------------------

    y = feature[target]

    X = feature.drop(columns=drop_cols)

    # --------------------------
    # Split
    # --------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # --------------------------
    # Train
    # --------------------------

    model.fit(
        X_train,
        y_train,
    )

    # --------------------------
    # Predict
    # --------------------------

    pred = model.predict(X_test)

    # --------------------------
    # Evaluate
    # --------------------------

    print("=" * 60)

    print(
        "Target:",
        target,
    )

    print()

    print(
        "Accuracy:",
        accuracy_score(
            y_test,
            pred,
        ),
    )

    print(
        "Balanced Accuracy:",
        balanced_accuracy_score(
            y_test,
            pred,
        ),
    )

    print()

    print(
        classification_report(
            y_test,
            pred,
            zero_division=0,
        )
    )

    # --------------------------
    # Top 5
    # --------------------------

    if hasattr(model, "predict_proba"):

        proba = model.predict_proba(X_test)

        classes = model.classes_

        top5_idx = np.argsort(
            proba,
            axis=1
        )[:, -5:]

        top5_pred = classes[top5_idx]

        top5 = np.mean([
            y in pred
            for y, pred in zip(
                y_test,
                top5_pred,
            )
        ])

        print()

        print(
            "Top5 Accuracy:",
            top5,
        )

    # --------------------------
    # Feature Importance
    # --------------------------

    importance = (
        pd.DataFrame(
            {
                "feature": X.columns,
                "importance": model.feature_importances_,
            }
        )
        .sort_values(
            "importance",
            ascending=False,
        )
    )

    print()

    print(importance)

    return (
        model,
        list(X.columns),
        importance,
    )
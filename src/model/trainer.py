import numpy as np
import pandas as pd
import time

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
)


def train_model(
    feature: pd.DataFrame,
    target: str,
    drop_cols: list,
    model,
):

    feature = feature.copy()

    # ==========================================
    # Remove singleton class
    # ==========================================

    count = feature[target].value_counts()

    valid_class = count[count >= 2].index

    removed = count[count < 2]

    if len(removed) > 0:

        print("=" * 60)
        print("Remove singleton class")
        print(removed)

    feature = feature[
        feature[target].isin(valid_class)
    ].copy()

    # ==========================================
    # Target
    # ==========================================

    y = feature[target]

    X = feature.drop(columns=drop_cols)
    # ==========================================
    # Split
    # ==========================================

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # ==========================================
    # Train
    # ==========================================

    start = time.time()

    model.fit(
        X_train,
        y_train,
    )

    train_time = time.time() - start

    # ==========================================
    # Predict
    # ==========================================

    pred = model.predict(X_test)

    metrics = {

        "accuracy": accuracy_score(
            y_test,
            pred,
        ),

        "balanced_accuracy": balanced_accuracy_score(
            y_test,
            pred,
        ),

        "precision": precision_score(
            y_test,
            pred,
            average="weighted",
            zero_division=0,
        ),

        "recall": recall_score(
            y_test,
            pred,
            average="weighted",
            zero_division=0,
        ),

        "f1": f1_score(
            y_test,
            pred,
            average="weighted",
            zero_division=0,
        ),

        "train_time": train_time,

        "top5_accuracy": None,
    }

    # ==========================================
    # Top5 Accuracy
    # ==========================================

    if hasattr(model, "predict_proba"):

        proba = model.predict_proba(X_test)

        classes = model.classes_

        k = min(5, len(classes))

        top_idx = np.argsort(
            proba,
            axis=1,
        )[:, -k:]

        top_pred = classes[top_idx]

        top5 = np.mean([

            truth in pred_set

            for truth, pred_set in zip(
                y_test,
                top_pred,
            )

        ])

        metrics["top5_accuracy"] = top5

    # ==========================================
    # Print Metric
    # ==========================================

    print("=" * 60)
    print("Target:", target)
    print()

    print(f"Accuracy           : {metrics['accuracy']:.4f}")
    print(f"Balanced Accuracy  : {metrics['balanced_accuracy']:.4f}")
    print(f"Precision          : {metrics['precision']:.4f}")
    print(f"Recall             : {metrics['recall']:.4f}")
    print(f"F1 Score           : {metrics['f1']:.4f}")

    if metrics["top5_accuracy"] is not None:
        print(f"Top5 Accuracy      : {metrics['top5_accuracy']:.4f}")

    print(f"Train Time         : {metrics['train_time']:.2f} sec")

    print()

    print(
        classification_report(
            y_test,
            pred,
            zero_division=0,
        )
    )

    # ==========================================
    # Feature Importance
    # ==========================================

    if hasattr(model, "feature_importances_"):

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
            .reset_index(drop=True)
        )

    else:

        importance = pd.DataFrame(
            {
                "feature": X.columns,
                "importance": 0,
            }
        )

    print()
    print(importance)

    return (
        model,
        list(X.columns),
        importance,
        metrics,
    )
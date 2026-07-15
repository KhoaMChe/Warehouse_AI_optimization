import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# ===========================
# Load dataset
# ===========================


df = pd.read_csv(
    "../../data/process/dataset.csv"
)

# ===========================
# Feature
# ===========================

drop_cols = [
    "san_pham_id",
    "day_chinh",
    "ty_le",
    "tang_chinh",
]

X = df.drop(columns=drop_cols)

y = df["tang_chinh"]

# ===========================
# Encode
# ===========================

X = pd.get_dummies(
    X,
    columns=[
        "abc_class",
        "loai_kho",
    ]
)

feature_columns = X.columns

# ===========================
# Split
# ===========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# ===========================
# Train
# ===========================

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

model.fit(
    X_train,
    y_train,
)

# ===========================
# Evaluate
# ===========================

pred = model.predict(X_test)

print()

print("=" * 50)

print(
    "Accuracy:",
    accuracy_score(
        y_test,
        pred,
    ),
)

print()

print(
    classification_report(
        y_test,
        pred,
    )
)

print()

print(
    confusion_matrix(
        y_test,
        pred,
    )
)

# ===========================
# Feature Importance
# ===========================

importance = (
    pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)

print()

print(importance.head(20))

# ===========================
# Save
# ===========================

# joblib.dump(model, "model.pkl")
# joblib.dump(feature_columns, "feature_columns.pkl")

print()

print("Done.")
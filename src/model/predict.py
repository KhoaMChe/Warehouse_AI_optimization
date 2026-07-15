import joblib
import pandas as pd

# ===========================
# Load
# ===========================

model = joblib.load(
    "model.pkl"
)

feature_columns = joblib.load(
    "feature_columns.pkl"
)

# ===========================
# Predict function
# ===========================

def predict(df):

    X = df.copy()

    X = pd.get_dummies(
        X,
        columns=[
            "abc_class",
            "loai_kho",
        ]
    )

    X = X.reindex(
        columns=feature_columns,
        fill_value=0,
    )

    return model.predict(X)
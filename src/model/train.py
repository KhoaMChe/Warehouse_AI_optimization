import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

from trainer import train_model


# ============================================
# Load dataset
# ============================================

df = pd.read_csv(
    "../../data/process/classic_feature.csv"
)

# ============================================
# Kho cần train
# ============================================

KHO_ID = 12473657

feature = (
    df.query("kho_id == @KHO_ID")
      .reset_index(drop=True)
)

# ============================================
# Thư mục lưu model
# ============================================

SAVE_DIR = f"../../models/{KHO_ID}"

os.makedirs(
    SAVE_DIR,
    exist_ok=True
)


drop_day = [
    "san_pham_id",
    "vi_tri_id",
    "day_ke_id",
    "ma_so_vi_tri",
    "kho_id",
    "abc_class",
]

day_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced",
    n_jobs=2,
)

day_model, day_columns, day_importance = train_model(
    feature=feature,
    target="day_ke_id",
    drop_cols=drop_day,
    model=day_model,
)

joblib.dump(
    day_model,
    f"{SAVE_DIR}/day.pkl",
)

joblib.dump(
    day_columns,
    f"{SAVE_DIR}/day_columns.pkl",
)

day_importance.to_csv(
    f"{SAVE_DIR}/day_importance.csv",
    index=False,
)

drop_tang = [
    "san_pham_id",
    "vi_tri_id",
    "tang",
    "ma_so_vi_tri",
    "kho_id",
    "abc_class",
]

tang_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced",
    n_jobs=2,
)

tang_model, tang_columns, tang_importance = train_model(
    feature=feature,
    target="tang",
    drop_cols=drop_tang,
    model=tang_model,
)

joblib.dump(
    tang_model,
    f"{SAVE_DIR}/tang.pkl",
)

joblib.dump(
    tang_columns,
    f"{SAVE_DIR}/tang_columns.pkl",
)

tang_importance.to_csv(
    f"{SAVE_DIR}/tang_importance.csv",
    index=False,
)

print()

print("=" * 60)
print("Training Completed")
print("=" * 60)
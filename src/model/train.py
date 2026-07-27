# import os
# import joblib
# import pandas as pd

# from sklearn.ensemble import RandomForestClassifier

# from trainer import train_model


# # ============================================
# # Load dataset
# # ============================================

# df = pd.read_csv(
#     "../../data/process/classic_feature.csv"
# )

# # ============================================
# # Kho cần train
# # ============================================

# KHO_ID = 12630830

# feature = (
#     df.query("kho_id == @KHO_ID")
#       .reset_index(drop=True)
# )

# # ============================================
# # Thư mục lưu model
# # ============================================

# SAVE_DIR = f"../../models/{KHO_ID}"

# os.makedirs(
#     SAVE_DIR,
#     exist_ok=True
# )


# drop_day = [
#     "san_pham_id",
#     "vi_tri_id",
#     "day_ke_id",
#     "ma_so_vi_tri",
#     "kho_id",
#     "abc_class",
# ]

# day_model = RandomForestClassifier(
#     n_estimators=100,
#     random_state=42,
#     class_weight="balanced",
#     n_jobs=2,
# )

# day_model, day_columns, day_importance = train_model(
#     feature=feature,
#     target="day_ke_id",
#     drop_cols=drop_day,
#     model=day_model,
# )

# joblib.dump(
#     day_model,
#     f"{SAVE_DIR}/day.pkl",
# )

# joblib.dump(
#     day_columns,
#     f"{SAVE_DIR}/day_columns.pkl",
# )

# day_importance.to_csv(
#     f"{SAVE_DIR}/day_importance.csv",
#     index=False,
# )

# drop_tang = [
#     "san_pham_id",
#     "vi_tri_id",
#     "tang",
#     "ma_so_vi_tri",
#     "kho_id",
#     "abc_class",
# ]

# tang_model = RandomForestClassifier(
#     n_estimators=100,
#     random_state=42,
#     class_weight="balanced",
#     n_jobs=2,
# )

# tang_model, tang_columns, tang_importance = train_model(
#     feature=feature,
#     target="tang",
#     drop_cols=drop_tang,
#     model=tang_model,
# )

# # joblib.dump(
# #     tang_model,
# #     f"{SAVE_DIR}/tang.pkl",
# # )

# # joblib.dump(
# #     tang_columns,
# #     f"{SAVE_DIR}/tang_columns.pkl",
# # )

# # tang_importance.to_csv(
# #     f"{SAVE_DIR}/tang_importance.csv",
# #     index=False,
# # )

# print()

# print("=" * 60)
# print("Training Completed")
# print("=" * 60)


import os
import time
import joblib
import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
)

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
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

drop_tang = [
    "san_pham_id",
    "vi_tri_id",
    "tang",
    "ma_so_vi_tri",
    "kho_id",
    "abc_class",
]
MODELS = {

    "RandomForest": RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        min_samples_leaf=5,
        min_samples_split=10,
        max_features="sqrt",
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    ),

    "ExtraTrees": ExtraTreesClassifier(

        n_estimators=300,

        random_state=42,

        class_weight="balanced",

        n_jobs=-1,

    ),

    "LightGBM": LGBMClassifier(

        objective="multiclass",

        n_estimators=300,

        learning_rate=0.05,

        random_state=42,

        class_weight="balanced",

        verbose=-1,

    ),

    "CatBoost": CatBoostClassifier(
        iterations=300,
        depth=8,
        learning_rate=0.05,
        task_type="GPU",
        devices="0",
        verbose=False,
    ),
}

def train_target(

    feature,

    target,

    drop_cols,

    save_dir,

):

    benchmark = []

    for name, model in MODELS.items():

        print()

        print("=" * 60)

        print(name)

        start = time.time()

        clf, columns, importance, metrics = train_model(

            feature=feature,

            target=target,

            drop_cols=drop_cols,

            model=model,

        )

        elapsed = time.time() - start

        model_dir = os.path.join(

            save_dir,

            name,

        )

        os.makedirs(

            model_dir,

            exist_ok=True,

        )

        joblib.dump(

            clf,

            os.path.join(

                model_dir,

                f"{target}.pkl",

            ),

        )

        joblib.dump(

            columns,

            os.path.join(

                model_dir,

                f"{target}_columns.pkl",

            ),

        )

        importance.to_csv(

            os.path.join(

                model_dir,

                f"{target}_importance.csv",

            ),

            index=False,

        )

        benchmark.append(

            {

                "model": name,

                **metrics,

            }

        )

    return pd.DataFrame(benchmark)

day_result = train_target(

    feature,

    target="day_ke_id",

    drop_cols=drop_day,

    save_dir=SAVE_DIR,

)

tang_result = train_target(

    feature,

    target="tang",

    drop_cols=drop_tang,

    save_dir=SAVE_DIR,

)

benchmark = (

    day_result

    .merge(

        tang_result,

        on="model",

        suffixes=(

            "_day",

            "_tang",

        ),

    )

)

benchmark.to_csv(

    os.path.join(

        SAVE_DIR,

        "benchmark.csv",

    ),

    index=False,

)

print()

print("=" * 60)

print("Training Finished")

print("=" * 60)
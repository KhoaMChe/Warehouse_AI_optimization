from pathlib import Path

import pandas as pd

from predictor import Predictor
from ranking import rank_position

# ==========================================================
# Path
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# Load data
# ==========================================================

feature_table = pd.read_csv(
    BASE_DIR / "../../data/process/classic_feature.csv",
    low_memory=False,
)

vitri = pd.read_csv(
    BASE_DIR / "../../data/clean/dm_vi_tri_clean.csv",
    low_memory=False,
)

tonkho = pd.read_csv(
    BASE_DIR / "../../data/clean/xnk_ton_kho_clean.csv",
    low_memory=False,
)

cham = pd.read_csv(
    BASE_DIR / "../../data/clean/log_cham_hang.csv",
    low_memory=False,
)

product_table = pd.read_csv(
    BASE_DIR / "../../data/clean/dm_san_pham_clean.csv",
    low_memory=False,
)

# ==========================================================
# Predictor
# ==========================================================

predictor = Predictor(
    feature_table=feature_table,
    model_root=BASE_DIR / "../../models",
)

predictor.load_model(
    kho_id=12473657
)

# ==========================================================
# Test SKU
# ==========================================================

product = {
    "auto_id": 99999999,
    "kho_id": 12473657,
    "nganh_hang_id": 18,
    "gw_san_pham": 1.5,
    "cbm_san_pham": 0.006,
    "so_ngay_su_dung": 365,
    "tong_nhap": 300,
}

# ==========================================================
# Predictor
# ==========================================================

result = predictor.predict(
    product,
    target_vi_tri_type_id=2,  # Reserve, cho module Putaway
)

print("=" * 60)
print("DAY")
print(result["day_prediction"])

print()
print("TANG")
print(result["tang_prediction"])

# ==========================================================
# Ranking
# ==========================================================

ranking = rank_position(
    predictor_result=result,
    product=product,
    vitri=vitri,
    tonkho=tonkho,
    cham=cham,
    top_k=5,
    target_vi_tri_type_id=2,  # đồng bộ với ranking.py đã sửa trước đó
)

print()
print("=" * 60)
print("TOP 5 POSITION")

if ranking.empty:

    print("Không tìm thấy vị trí phù hợp.")

else:

    cols = [
        "auto_id",
        "ma_so_vi_tri",
        "day_ke_id",
        "tang",
        "score",
        "same_product",
        "empty",
    ]

    print(ranking[cols])
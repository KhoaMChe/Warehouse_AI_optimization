from pathlib import Path
import pandas as pd

from rule_ranking import rank_position

BASE_DIR = Path(__file__).resolve().parent

# ==============================
# Load dữ liệu
# ==============================

vitri = pd.read_csv(
    BASE_DIR / "../data/clean/12473657/vi_tri_kho12473657.csv"
)

tonkho = pd.read_csv(
    BASE_DIR / "../data/clean/xnk_ton_kho_clean.csv"
)

cham = pd.read_csv(
    BASE_DIR / "../data/clean/log_cham_hang.csv"
)

# ==============================
# Sản phẩm test
# ==============================

product = {
    "auto_id": 40000001,              # thay bằng id thật
    "kho_id": 12473657,
    "nganh_hang_id": 12501018,
    "gw_san_pham": 14.2,
    "cbm_san_pham": 39368,
    "so_ngay_su_dung": 0,
    "tong_nhap": 300,
}

# ==============================
# Ranking
# ==============================

result = rank_position(
    product=product,
    vitri=vitri,
    tonkho=tonkho,
    cham=cham,
    top_k=10,
)

print(result[
    [
        "ma_so_vi_tri",
        "day_ke_id",
        "tang",
        "score",
    ]
])
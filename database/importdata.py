import pandas as pd
from setup_database import migrate_from_dataframes
dfs = {
    "sanpham": pd.read_csv("../data/clean/dm_san_pham_clean.csv"),
    "vitri": pd.read_csv("../data/clean//dm_vi_tri_clean.csv"),
    "tonkho": pd.read_csv("../data/clean/xnk_ton_kho_clean.csv"),
    "nhapkho": pd.read_csv("../data/clean/xnk_nhap_kho_clean.csv"),
    "xuatkho": pd.read_csv("../data/clean/xnk_xuat_kho_clean.csv"),
    "cham": pd.read_csv("../data/clean/log_cham_hang.csv"),
}

migrate_from_dataframes(dfs)
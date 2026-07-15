import pandas as pd
import numpy as np


def create_inventory_feature(
    nhapkho,
    tonkho
):

    nhapkho = nhapkho.copy()
    tonkho = tonkho.copy()

    nhapkho["tong_nhap"] = (
        nhapkho["sl_nhap_chan"].fillna(0)
        + nhapkho["sl_nhap_le"].fillna(0)
        + nhapkho["sl_nhap_all_special"].fillna(0)
    )

    tong_nhap = (
        nhapkho
        .groupby("san_pham_id")["tong_nhap"]
        .sum()
    )

    tonkho["ton_kho"] = (
        tonkho["sl_nhap_chan"].fillna(0)
        + tonkho["sl_nhap_le"].fillna(0)
        + tonkho["sl_nhap_all_special"].fillna(0)
        - tonkho["sl_xuat_chan"].fillna(0)
        - tonkho["sl_xuat_le"].fillna(0)
        - tonkho["sl_xuat_all_special"].fillna(0)
    )

    ton = (
        tonkho
        .groupby("san_pham_id")["ton_kho"]
        .sum()
    )

    return (
        pd.concat(
            [tong_nhap, ton],
            axis=1
        )
        .reset_index()
    )

def create_outbound_feature(xuatkho):
    xuatkho = xuatkho.copy()

    # ==========================
    # Tổng số lượng xuất
    # ==========================

    xuatkho["tong_xuat"] = (
        xuatkho["sl_allocated_chan"].fillna(0)
        + xuatkho["sl_allocated_le"].fillna(0)
        + xuatkho["sl_allocated_all_special"].fillna(0)
    )

    feature = (
        xuatkho
        .groupby("san_pham_id", as_index=False)
        .agg(
            tong_xuat=("tong_xuat", "sum"),
            tan_suat_xuat=("tong_xuat", "count"),
        )
    )

    # ==========================
    # Phân loại ABC (Pareto)
    # ==========================

    abc = feature.sort_values(
        "tong_xuat",
        ascending=False
    ).copy()

    total = abc["tong_xuat"].sum()

    if total > 0:
        abc["cum_ratio"] = abc["tong_xuat"].cumsum() / total
    else:
        abc["cum_ratio"] = 0

    def classify(x):
        if x <= 0.80:
            return "A"
        elif x <= 0.95:
            return "B"
        else:
            return "C"

    abc["abc_class"] = abc["cum_ratio"].apply(classify)

    # Dùng cho ML
    abc["abc_score"] = abc["abc_class"].map({
        "A": 3,
        "B": 2,
        "C": 1
    })

    return abc[
        [
            "san_pham_id",
            "tong_xuat",
            "tan_suat_xuat",
            "abc_class",
            "abc_score",
        ]
    ]

def create_product_feature(sanpham):

    product = sanpham.rename(
        columns={"auto_id": "san_pham_id"}
    ).copy()

    return product[
        [
            "san_pham_id",
            "nganh_hang_id",
            "gw_san_pham",
            "cbm_san_pham",
            "so_ngay_su_dung"
        ]
    ]

def create_replenishment_feature(
    cham,
    outbound
):

    rep = (
        cham
        .groupby("san_pham_id")
        .size()
        .rename("so_lan_cham")
        .reset_index()
    )

    rep = rep.merge(
        outbound[
            [
                "san_pham_id",
                "tan_suat_xuat"
            ]
        ],
        how="left"
    )

    rep["ti_le_cham_hang"] = (
        rep["so_lan_cham"]
        / rep["tan_suat_xuat"]
    )

    rep["ti_le_cham_hang"] = (
        rep["ti_le_cham_hang"]
        .replace(np.inf,0)
        .fillna(0)
    )

    return rep[
        [
            "san_pham_id",
            "ti_le_cham_hang"
        ]
    ]

def create_temporal_feature(nhapkho):

    nhapkho = nhapkho.copy()

    date_cols = [
        "ngay_san_xuat",
        "ngay_het_han",
        "ngay_nhap_kho_root",
    ]

    for col in date_cols:
        nhapkho[col] = pd.to_datetime(
            nhapkho[col],
            errors="coerce"
        )

    # Mốc thời gian cuối cùng trong dataset
    reference_date = nhapkho["ngay_nhap_kho_root"].max()

    # Tổng thời hạn sử dụng
    nhapkho["shelf_life_days"] = (
        nhapkho["ngay_het_han"]
        - nhapkho["ngay_san_xuat"]
    ).dt.days

    # Thời hạn còn lại khi nhập kho
    nhapkho["remaining_shelf_life_days"] = (
        nhapkho["ngay_het_han"]
        - nhapkho["ngay_nhap_kho_root"]
    ).dt.days

    # Tuổi tồn kho tính đến ngày cuối dataset
    nhapkho["inventory_age_days"] = (
        reference_date
        - nhapkho["ngay_nhap_kho_root"]
    ).dt.days

    feature = (
        nhapkho
        .groupby("san_pham_id", as_index=False)
        .agg(
            shelf_life_days=("shelf_life_days", "mean"),
            remaining_shelf_life_days=("remaining_shelf_life_days", "mean"),
            inventory_age_days=("inventory_age_days", "mean"),
        )
    )

    return feature

def build_location_feature(
    tonkho,
    vitri,
):
    """
    Feature theo vị trí.
    """

    location = (
        tonkho
        .groupby("vi_tri_id")
        .agg(
            tong_ton=("sl_nhap_chan", "sum"),
            so_sku=("san_pham_id", "nunique"),
            so_lpn=("so_lpn", "nunique")
        )
        .reset_index()
    )

    location = location.merge(
        vitri,
        on="vi_tri_id",
        how="left"
    )

    return location

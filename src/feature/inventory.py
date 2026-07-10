import pandas as pd


def create_inventory_feature(nhapkho, tonkho):

    # ==========================
    # Tổng nhập
    # ==========================

    nhapkho = nhapkho.copy()

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

    # ==========================
    # Tồn kho
    # ==========================

    tonkho = tonkho.copy()

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

    feature = pd.concat(
        [tong_nhap, ton],
        axis=1
    ).reset_index()

    return feature
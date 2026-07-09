import pandas as pd


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

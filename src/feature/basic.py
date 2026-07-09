import pandas as pd


def build_basic_feature(
    sanpham: pd.DataFrame,
    tonkho: pd.DataFrame,
    xuatkho: pd.DataFrame,
    cham: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tạo feature cơ bản theo SKU.

    Output:
        1 dòng = 1 SKU
    """

    # ==========================================================
    # COPY DATA
    # ==========================================================

    tonkho = tonkho.copy()
    xuatkho = xuatkho.copy()
    cham = cham.copy()

    # ==========================================================
    # TÍNH TỔNG SỐ LƯỢNG XUẤT (ALLOCATED)
    # ==========================================================

    xuatkho["tong_xuat"] = (
        xuatkho["sl_allocated_chan"].fillna(0)
        + xuatkho["sl_allocated_le"].fillna(0)
        + xuatkho["sl_allocated_all_special"].fillna(0)
    )

    # ==========================================================
    # TÍNH TỔNG SỐ LƯỢNG CHÂM
    # ==========================================================

    cham["tong_cham"] = (
        cham["sl_repleshniment_chan"].fillna(0)
        + cham["sl_repleshniment_le"].fillna(0)
        + cham["sl_repleshniment_all_special"].fillna(0)
    )

    # ==========================================================
    # FEATURE TỒN KHO
    # ==========================================================

    stock_feature = (
        tonkho
        .groupby("san_pham_id")
        .agg(
            tong_ton=("sl_nhap_chan", "sum"),

            tong_xuat_thuc_te=("sl_xuat_chan", "sum"),

            so_lpn=("so_lpn", "nunique"),

            so_vi_tri=("vi_tri_id", "nunique"),

            tong_so_kien=("so_kien_nhap", "sum"),

            tong_gw=("gw", "sum"),

            tong_nw=("nw", "sum"),

            tong_cbm=("cbm", "sum")
        )
        .reset_index()
    )

    # ==========================================================
    # FEATURE XUẤT KHO
    # ==========================================================

    outbound_feature = (
        xuatkho
        .groupby("san_pham_id")
        .agg(
            tong_xuat=("tong_xuat", "sum"),

            so_lan_xuat=("tong_xuat", "count"),

            so_don_xuat=("xuat_kho_id", "nunique"),

            so_lpn_da_xuat=("so_lpn", "nunique")
        )
        .reset_index()
    )

    # ==========================================================
    # FEATURE CHÂM HÀNG
    # ==========================================================

    replenish_feature = (
        cham
        .groupby("san_pham_id")
        .agg(
            tong_cham=("tong_cham", "sum"),

            so_lan_cham=("tong_cham", "count"),

            so_lpn_cham=("so_lpn", "nunique")
        )
        .reset_index()
    )

    # ==========================================================
    # THÔNG TIN SKU
    # ==========================================================

    product_feature = sanpham.copy()

    # ==========================================================
    # MERGE
    # ==========================================================
    # Đổi khóa chính để thống nhất với các bảng khác
    product_feature = product_feature.rename(
        columns={"auto_id": "san_pham_id"}
    )
    feature = (
        product_feature
        .merge(stock_feature, on="san_pham_id", how="left")
        .merge(outbound_feature, on="san_pham_id", how="left")
        .merge(replenish_feature, on="san_pham_id", how="left")
    )

    # ==========================================================
    # FILL NA
    # ==========================================================

    numeric_cols = feature.select_dtypes(include="number").columns

    feature[numeric_cols] = feature[numeric_cols].fillna(0)

    return feature
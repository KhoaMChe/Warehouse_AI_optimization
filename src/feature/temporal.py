import pandas as pd


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
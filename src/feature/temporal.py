def build_temporal_feature(xuatkho):

    temp = (
        xuatkho
        .groupby("san_pham_id")
        .agg(
            ngay_xuat_cuoi=("ngay_san_xuat","max"),
            ngay_xuat_dau=("ngay_het_han","min")
        )
        .reset_index()
    )

    return temp
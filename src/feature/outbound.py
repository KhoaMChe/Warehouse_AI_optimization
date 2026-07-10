import pandas as pd


def create_outbound_feature(xuatkho):

    xuatkho = xuatkho.copy()

    xuatkho["tong_xuat"] = (
        xuatkho["sl_allocated_chan"].fillna(0)
        + xuatkho["sl_allocated_le"].fillna(0)
        + xuatkho["sl_allocated_all_special"].fillna(0)
    )

    tong_xuat = (
        xuatkho
        .groupby("san_pham_id")["tong_xuat"]
        .sum()
    )

    tan_suat = (
        xuatkho
        .groupby("san_pham_id")
        .size()
        .rename("tan_suat_xuat")
    )

    feature = pd.concat(
        [tong_xuat, tan_suat],
        axis=1
    ).reset_index()

    # ======================
    # ABC
    # ======================

    abc = feature.sort_values(
        "tong_xuat",
        ascending=False
    )

    abc["cum_ratio"] = (
        abc["tong_xuat"].cumsum()
        / abc["tong_xuat"].sum()
    )

    def classify(x):

        if x <= 0.8:
            return "A"

        elif x <= 0.95:
            return "B"

        return "C"

    abc["abc_class"] = abc["cum_ratio"].apply(classify)

    return abc.drop(columns="cum_ratio")
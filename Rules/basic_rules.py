import pandas as pd

def rule_same_product(candidate):

    candidate.loc[
        candidate["same_product"],
        "score",
    ] += 200


def rule_empty_location(candidate):

    candidate.loc[
        candidate["empty"],
        "score",
    ] += 100

def rule_replenishment(candidate, cham):

    replenish = pd.concat(
        [
            cham["vi_tri_moi_id"],
        ]
    ).dropna().unique()

    candidate.loc[
        candidate["auto_id"].isin(replenish),
        "score",
    ] -= 200

def rule_heavy_product(candidate, product):

    gw = product["gw_san_pham"]

    if gw < 30:
        return

    candidate.loc[
        candidate["tang"] == 1,
        "score",
    ] += 40

    candidate.loc[
        candidate["tang"] == 2,
        "score",
    ] += 20

    candidate.loc[
        candidate["tang"] >= 3,
        "score",
    ] -= 50

def rule_large_volume(candidate, product):

    cbm = product["cbm_san_pham"]

    if cbm < 50000:
        return

    candidate.loc[
        candidate["tang"] == 1,
        "score",
    ] += 35

    candidate.loc[
        candidate["tang"] >= 3,
        "score",
    ] -= 30

def rule_short_expiry(candidate, product):

    days = product["so_ngay_su_dung"]

    if days > 60:
        return

    candidate.loc[
        candidate["tang"] == 1,
        "score",
    ] += 20

    candidate.loc[
        candidate["tang"] >= 3,
        "score",
    ] -= 20

def rule_balance_day(candidate, tonkho):

    load = (
        tonkho
        .merge(
            candidate[
                [
                    "auto_id",
                    "day_ke_id",
                ]
            ],
            left_on="vi_tri_id",
            right_on="auto_id",
            how="right",
        )
        .groupby("day_ke_id")
        .size()
    )

    candidate["day_load"] = (
        candidate["day_ke_id"]
        .map(load)
        .fillna(0)
    )

    candidate["score"] -= (
        candidate["day_load"] * 0.2
    )

def rule_same_category(candidate, product):

    if "nganh_hang_id" not in candidate.columns:
        return

    candidate.loc[
        candidate["nganh_hang_id"] == product["nganh_hang_id"],
        "score",
    ] += 40
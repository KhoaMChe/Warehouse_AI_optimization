import pandas as pd

from rule_engine import RuleEngine


def rank_position(
    product: dict,
    vitri: pd.DataFrame,
    tonkho: pd.DataFrame,
    cham: pd.DataFrame,
    top_k: int = 5,
):

    kho_id = product["kho_id"]
    san_pham_id = product["auto_id"]


    candidate = (
        vitri[
            vitri["kho_id"] == kho_id
        ]
        .copy()
    )

    if candidate.empty:
        return pd.DataFrame()


    occupied = (
        tonkho[
            [
                "vi_tri_id",
                "san_pham_id",
            ]
        ]
        .drop_duplicates()
    )

    candidate = candidate.merge(
        occupied,
        left_on="auto_id",
        right_on="vi_tri_id",
        how="left",
    )

    candidate.rename(
        columns={
            "san_pham_id": "sku_current",
        },
        inplace=True,
    )

    candidate["same_product"] = (
        candidate["sku_current"] == san_pham_id
    )

    candidate["empty"] = (
        candidate["sku_current"].isna()
    )

    candidate["other_product"] = (
        (~candidate["same_product"])
        &
        (~candidate["empty"])
    )

    candidate = candidate[
        ~candidate["other_product"]
    ]

    if candidate.empty:
        return pd.DataFrame()

    engine = RuleEngine()

    candidate = engine.apply(
        candidate=candidate,
        product=product,
        tonkho=tonkho,
        cham=cham,
    )


    result = (
        candidate
        .sort_values(
            "score",
            ascending=False,
        )
        .drop_duplicates(
            subset="auto_id"
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    return result
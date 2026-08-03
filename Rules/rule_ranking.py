import pandas as pd

from rule_engine import RuleEngine


def rank_position(
    product: dict,
    vitri: pd.DataFrame,
    tonkho: pd.DataFrame,
    cham: pd.DataFrame,
    top_k: int = 5,
):
    """
    Ranking vị trí hoàn toàn dựa trên Rule Engine.

    Parameters
    ----------
    product : dict
        Thông tin sản phẩm nhập kho.

    vitri : DataFrame
        Danh mục vị trí.

    tonkho : DataFrame
        Tồn kho hiện tại.

    cham : DataFrame
        Log châm hàng.

    Returns
    -------
    Top K vị trí tốt nhất.
    """

    kho_id = product["kho_id"]
    san_pham_id = product["auto_id"]

    # =====================================================
    # Candidate theo kho
    # =====================================================

    candidate = (
        vitri[
            vitri["kho_id"] == kho_id
        ]
        .copy()
    )

    if candidate.empty:
        return pd.DataFrame()

    # =====================================================
    # Merge tồn kho
    # =====================================================

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

    # =====================================================
    # Flag
    # =====================================================

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

    # =====================================================
    # Không overwrite SKU khác
    # =====================================================

    candidate = candidate[
        ~candidate["other_product"]
    ]

    if candidate.empty:
        return pd.DataFrame()

    # =====================================================
    # Rule Engine
    # =====================================================

    engine = RuleEngine()

    candidate = engine.apply(
        candidate=candidate,
        product=product,
        tonkho=tonkho,
        cham=cham,
    )

    # =====================================================
    # Ranking
    # =====================================================

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
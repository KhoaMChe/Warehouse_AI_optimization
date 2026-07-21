import pandas as pd


def rank_position(
    predictor_result: dict,
    product: dict,
    vitri: pd.DataFrame,
    tonkho: pd.DataFrame,
    cham: pd.DataFrame,
    top_k: int = 5,
):

    kho_id = product["kho_id"]
    san_pham_id = product["auto_id"]

    day_prediction = predictor_result["day_prediction"]

    tang_prediction = predictor_result["tang_prediction"]

    results = []

    # =====================================================
    # Duyệt tất cả Day
    # =====================================================

    for _, day_row in day_prediction.iterrows():

        day_ke_id = day_row["day_ke_id"]
        day_prob = day_row["probability"]

        # =================================================
        # Duyệt tất cả Tang
        # =================================================

        for _, tang_row in tang_prediction.iterrows():

            tang = tang_row["tang"]
            tang_prob = tang_row["probability"]

            # =============================================
            # Candidate
            # =============================================

            candidate = vitri[
                (vitri["kho_id"] == kho_id)
                &
                (vitri["day_ke_id"] == day_ke_id)
                &
                (vitri["tang"] == tang)
            ].copy()

            if candidate.empty:
                continue

            # =============================================
            # Vị trí đang có tồn
            # =============================================

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
                    "san_pham_id": "sku_current"
                },
                inplace=True,
            )

            # =============================================
            # Flag
            # =============================================

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

            # =============================================
            # Loại SKU khác
            # =============================================

            candidate = candidate[
                ~candidate["other_product"]
            ]

            if candidate.empty:
                continue

            # =============================================
            # Loại vị trí châm
            # =============================================

            replenish = pd.concat(
                [
                    cham["vi_tri_cu_id"],
                    cham["vi_tri_moi_id"],
                ]
            ).dropna().unique()

            candidate = candidate[
                ~candidate["auto_id"].isin(
                    replenish
                )
            ]

            if candidate.empty:
                continue

            # =============================================
            # Score
            # =============================================

            candidate["score"] = 0.0

            # cùng SKU
            candidate.loc[
                candidate["same_product"],
                "score",
            ] += 100

            # vị trí trống
            candidate.loc[
                candidate["empty"],
                "score",
            ] += 50

            # xác suất AI
            candidate["score"] += (
                day_prob * 30
            )

            candidate["score"] += (
                tang_prob * 20
            )

            candidate["day_probability"] = day_prob

            candidate["tang_probability"] = tang_prob

            results.append(candidate)

    # =====================================================
    # Không có candidate
    # =====================================================

    if len(results) == 0:

        return pd.DataFrame()

    # =====================================================
    # Merge
    # =====================================================

    result = pd.concat(
        results,
        ignore_index=True,
    )

    # =====================================================
    # Trùng vị trí
    # =====================================================

    result = (
        result
        .sort_values(
            "score",
            ascending=False,
        )
        .drop_duplicates(
            subset="auto_id"
        )
    )

    # =====================================================
    # Top K
    # =====================================================

    return result.head(top_k)
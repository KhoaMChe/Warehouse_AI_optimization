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
                    #cham["vi_tri_cu_id"],
                    cham["vi_tri_moi_id"],
                ]
            ).dropna().unique()

            if candidate.empty:
                continue

            # =============================================
            # Score
            # =============================================

            candidate["score"] = 0.0

            candidate.loc[
                candidate["auto_id"].isin(replenish),
                "score",
            ] -= 200
            
            # cùng SKU
            candidate.loc[
                candidate["same_product"],
                "score",
            ] += 200

            # vị trí trống ưu tiên
            candidate.loc[
                candidate["empty"],
                "score",
            ] += 100

            # xác suất AI
            candidate["score"] += (
                day_prob * 50
            )

            candidate["score"] += (
                tang_prob * 40
            )

            candidate["day_probability"] = day_prob

            candidate["tang_probability"] = tang_prob

            results.append(candidate)

            #hàng nặng tầng thấp
            gw = product["gw_san_pham"]

            if gw >= 30:

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

                #hàng cồng kềnh tầng thấp 
            cbm = product["cbm_san_pham"]

            if cbm >= 0.10:

                candidate.loc[
                    candidate["tang"] == 1,
                    "score",
                ] += 35

                candidate.loc[
                    candidate["tang"] >= 3,
                    "score",
                ] -= 30

            #Hàng HSD sắp hết < 60 ngày 
            if product["so_ngay_su_dung"] <= 60:

                candidate.loc[
                    candidate["tang"] == 1,
                    "score",
                ] += 20

                candidate.loc[
                    candidate["tang"] >= 3,
                    "score",
                ] -= 20
            #dãy quá nhiều sku và pallet giảm điểm ưu tiên dãy trống
            day_count = tonkho.merge(
                vitri[
                    [
                        "auto_id",
                        "day_ke_id",
                    ]
                ],
                left_on="vi_tri_id",
                right_on="auto_id",
            )

            load = (
                day_count
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
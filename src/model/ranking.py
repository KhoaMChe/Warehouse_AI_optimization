# import pandas as pd


# def rank_position(
#     predictor_result: dict,
#     product: dict,
#     vitri: pd.DataFrame,
#     tonkho: pd.DataFrame,
#     cham: pd.DataFrame,
#     top_k: int = 5,
# ):

#     kho_id = product["kho_id"]
#     san_pham_id = product["auto_id"]

#     day_prediction = predictor_result["day_prediction"]

#     tang_prediction = predictor_result["tang_prediction"]

#     results = []

#     # =====================================================
#     # Duyệt tất cả Day
#     # =====================================================

#     for _, day_row in day_prediction.iterrows():

#         day_ke_id = day_row["day_ke_id"]
#         day_prob = day_row["probability"]

#         # =================================================
#         # Duyệt tất cả Tang
#         # =================================================

#         for _, tang_row in tang_prediction.iterrows():

#             tang = tang_row["tang"]
#             tang_prob = tang_row["probability"]

#             # =============================================
#             # Candidate
#             # =============================================

#             candidate = vitri[
#                 (vitri["kho_id"] == kho_id)
#                 &
#                 (vitri["day_ke_id"] == day_ke_id)
#                 &
#                 (vitri["tang"] == tang)
#             ].copy()

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Vị trí đang có tồn
#             # =============================================

#             occupied = (
#                 tonkho[
#                     [
#                         "vi_tri_id",
#                         "san_pham_id",
#                     ]
#                 ]
#                 .drop_duplicates()
#             )

#             candidate = candidate.merge(
#                 occupied,
#                 left_on="auto_id",
#                 right_on="vi_tri_id",
#                 how="left",
#             )

#             candidate.rename(
#                 columns={
#                     "san_pham_id": "sku_current"
#                 },
#                 inplace=True,
#             )

#             # =============================================
#             # Flag
#             # =============================================

#             candidate["same_product"] = (
#                 candidate["sku_current"] == san_pham_id
#             )

#             candidate["empty"] = (
#                 candidate["sku_current"].isna()
#             )

#             candidate["other_product"] = (
#                 (~candidate["same_product"])
#                 &
#                 (~candidate["empty"])
#             )

#             # =============================================
#             # Loại SKU khác
#             # =============================================

#             candidate = candidate[
#                 ~candidate["other_product"]
#             ]

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Loại vị trí châm
#             # =============================================

#             replenish = pd.concat(
#                 [
#                     #cham["vi_tri_cu_id"],
#                     cham["vi_tri_moi_id"],
#                 ]
#             ).dropna().unique()

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Score
#             # =============================================

#             candidate["score"] = 0.0

#             candidate.loc[
#                 candidate["auto_id"].isin(replenish),
#                 "score",
#             ] -= 20
            
#             # cùng SKU
#             candidate.loc[
#                 candidate["same_product"],
#                 "score",
#             ] += 20

#             # vị trí trống ưu tiên
#             candidate.loc[
#                 candidate["empty"],
#                 "score",
#             ] += 10

#             # xác suất AI
#             candidate["score"] += (
#                 day_prob * 60
#             )

#             candidate["score"] += (
#                 tang_prob * 50
#             )

#             candidate["day_probability"] = day_prob

#             candidate["tang_probability"] = tang_prob

#             results.append(candidate)

#             #hàng nặng tầng thấp
#             gw = product["gw_san_pham"]

#             if gw >= 30:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 10

#                 candidate.loc[
#                     candidate["tang"] == 2,
#                     "score",
#                 ] += 5

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= 8

#                 #hàng cồng kềnh tầng thấp 
#             cbm = product["cbm_san_pham"]

#             if cbm >= 25000:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 5

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= 10

#             #Hàng HSD sắp hết < 60 ngày 
#             if product["so_ngay_su_dung"] <= 60:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 10

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= 20
#             #dãy quá nhiều sku và pallet giảm điểm ưu tiên dãy trống
#             day_count = tonkho.merge(
#                 vitri[
#                     [
#                         "auto_id",
#                         "day_ke_id",
#                     ]
#                 ],
#                 left_on="vi_tri_id",
#                 right_on="auto_id",
#             )

#             load = (
#                 day_count
#                 .groupby("day_ke_id")
#                 .size()
#             )

#             candidate["day_load"] = (
#                 candidate["day_ke_id"]
#                 .map(load)
#                 .fillna(0)
#             )

#             candidate["score"] -= (
#                 candidate["day_load"] * 0.2
#             )
#     # =====================================================
#     # Không có candidate
#     # =====================================================

#     if len(results) == 0:

#         return pd.DataFrame()

#     # =====================================================
#     # Merge
#     # =====================================================

#     result = pd.concat(
#         results,
#         ignore_index=True,
#     )

#     # =====================================================
#     # Trùng vị trí
#     # =====================================================

#     result = (
#         result
#         .sort_values(
#             "score",
#             ascending=False,
#         )
#         .drop_duplicates(
#             subset="auto_id"
#         )
#     )

#     # =====================================================
#     # Top K
#     # =====================================================

#     return result.head(top_k)


# import pandas as pd


# def rank_position(
#     predictor_result: dict,
#     product: dict,
#     vitri: pd.DataFrame,
#     tonkho: pd.DataFrame,
#     cham: pd.DataFrame,
#     top_k: int = 5,
# ):

#     kho_id = product["kho_id"]
#     san_pham_id = product["auto_id"]

#     day_prediction = predictor_result["day_prediction"]

#     # tang_prediction giờ có cột day_ke_id gắn kèm (mỗi dãy có
#     # bộ tầng riêng, được predict đúng theo ngữ cảnh của dãy đó)
#     tang_prediction = predictor_result["tang_prediction"]

#     results = []

#     # =====================================================
#     # day_load: tính 1 lần duy nhất trước vòng lặp
#     # (trước đây bị tính lại ở mỗi cặp day x tang -> lãng phí)
#     # =====================================================

#     day_count = tonkho.merge(
#         vitri[
#             [
#                 "auto_id",
#                 "day_ke_id",
#             ]
#         ],
#         left_on="vi_tri_id",
#         right_on="auto_id",
#     )

#     day_load_map = (
#         day_count
#         .groupby("day_ke_id")
#         .size()
#     )

#     # =====================================================
#     # Duyệt Day (top_day dãy do model dự đoán)
#     # =====================================================

#     for _, day_row in day_prediction.iterrows():

#         day_ke_id = day_row["day_ke_id"]
#         day_prob = day_row["probability"]

#         # =================================================
#         # Chỉ lấy các tầng ĐÃ ĐƯỢC PREDICT CHO ĐÚNG DÃY NÀY
#         # (trước đây loop qua toàn bộ tang_prediction bất kể
#         # nó được sinh ra cho dãy nào -> sai ngữ cảnh)
#         # =================================================

#         tang_for_this_day = tang_prediction[
#             tang_prediction["day_ke_id"] == day_ke_id
#         ]

#         for _, tang_row in tang_for_this_day.iterrows():

#             tang = tang_row["tang"]
#             tang_prob = tang_row["probability"]

#             # =============================================
#             # Candidate
#             # =============================================

#             candidate = vitri[
#                 (vitri["kho_id"] == kho_id)
#                 &
#                 (vitri["day_ke_id"] == day_ke_id)
#                 &
#                 (vitri["tang"] == tang)
#             ].copy()

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Vị trí đang có tồn
#             # =============================================

#             occupied = (
#                 tonkho[
#                     [
#                         "vi_tri_id",
#                         "san_pham_id",
#                     ]
#                 ]
#                 .drop_duplicates()
#             )

#             candidate = candidate.merge(
#                 occupied,
#                 left_on="auto_id",
#                 right_on="vi_tri_id",
#                 how="left",
#             )

#             candidate.rename(
#                 columns={
#                     "san_pham_id": "sku_current"
#                 },
#                 inplace=True,
#             )

#             # =============================================
#             # Flag
#             # =============================================

#             candidate["same_product"] = (
#                 candidate["sku_current"] == san_pham_id
#             )

#             candidate["empty"] = (
#                 candidate["sku_current"].isna()
#             )

#             candidate["other_product"] = (
#                 (~candidate["same_product"])
#                 &
#                 (~candidate["empty"])
#             )

#             # =============================================
#             # Loại SKU khác
#             # =============================================

#             candidate = candidate[
#                 ~candidate["other_product"]
#             ]

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Loại vị trí châm
#             # =============================================

#             replenish = pd.concat(
#                 [
#                     #cham["vi_tri_cu_id"],
#                     cham["vi_tri_moi_id"],
#                 ]
#             ).dropna().unique()

#             if candidate.empty:
#                 continue

#             # =============================================
#             # Score
#             # =============================================

#             candidate["score"] = 0.0

#             candidate.loc[
#                 candidate["auto_id"].isin(replenish),
#                 "score",
#             ] -= 20
            
#             # cùng SKU
#             candidate.loc[
#                 candidate["same_product"],
#                 "score",
#             ] += 20

#             # vị trí trống ưu tiên
#             candidate.loc[
#                 candidate["empty"],
#                 "score",
#             ] += 10

#             # xác suất AI
#             candidate["score"] += (
#                 day_prob * 60
#             )

#             candidate["score"] += (
#                 tang_prob * 50
#             )

#             candidate["day_probability"] = day_prob

#             candidate["tang_probability"] = tang_prob

#             results.append(candidate)

#             #hàng nặng tầng thấp
#             gw = product["gw_san_pham"]

#             if gw >= 30:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 5

#                 candidate.loc[
#                     candidate["tang"] == 2,
#                     "score",
#                 ] += 5

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= -8

#                 #hàng cồng kềnh tầng thấp 
#             cbm = product["cbm_san_pham"]

#             if cbm >= 25000:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 5

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= 10

#             #Hàng HSD sắp hết < 60 ngày 
#             if product["so_ngay_su_dung"] <= 60:

#                 candidate.loc[
#                     candidate["tang"] == 1,
#                     "score",
#                 ] += 10

#                 candidate.loc[
#                     candidate["tang"] >= 4,
#                     "score",
#                 ] -= 5
#             #dãy quá nhiều sku và pallet giảm điểm ưu tiên dãy trống
#             candidate["day_load"] = (
#                 candidate["day_ke_id"]
#                 .map(day_load_map)
#                 .fillna(0)
#             )

#             candidate["score"] -= (
#                 candidate["day_load"] * 0.2
#             )
#     # =====================================================
#     # Không có candidate
#     # =====================================================

#     if len(results) == 0:

#         return pd.DataFrame()

#     # =====================================================
#     # Merge
#     # =====================================================

#     result = pd.concat(
#         results,
#         ignore_index=True,
#     )

#     # =====================================================
#     # Trùng vị trí
#     # =====================================================

#     result = (
#         result
#         .sort_values(
#             "score",
#             ascending=False,
#         )
#         .drop_duplicates(
#             subset="auto_id"
#         )
#     )

#     # =====================================================
#     # Top K
#     # =====================================================

#     return result.head(top_k)



import numpy as np
import pandas as pd


# ==============================================================
# Trọng số scoring — TẤT CẢ thành phần đều nằm trong [0,1] trước
# khi nhân trọng số, để không thành phần nào "nuốt" thành phần khác
# chỉ vì đơn vị đo khác nhau.
#
# Tinh chỉnh ở đây, không cần sửa logic bên dưới.
# ==============================================================

DEFAULT_WEIGHTS = {
    "same_product": 0.18,
    "empty": 0.07,
    "ai_probability": 0.25,
    "physical_fit": 0.10,
    "congestion": 0.08,
    "capacity": 0.17,
    "proximity": 0.10,
    "accessibility": 0.05,
}


def _physical_fit(tang: int, gw: float, cbm: float, hsd_days: float) -> float:
    """
    Gộp 3 rule (hàng nặng, cồng kềnh, sắp hết hạn -> ưu tiên tầng thấp)
    thành 1 điểm fit trong [0,1] thay vì 3 khối cộng/trừ điểm rời rạc
    có thể triệt tiêu lẫn nhau một cách khó kiểm soát.
    """

    # Mức độ "cần tầng thấp", cộng dồn theo số điều kiện thỏa mãn
    urgency = 0.0

    if gw >= 30:
        urgency += 1.0

    if cbm >= 0.10:
        urgency += 1.0

    if hsd_days <= 60:
        urgency += 1.0

    if urgency == 0:
        # Không có ràng buộc vật lý đặc biệt -> mọi tầng như nhau
        return 0.5

    # urgency càng cao thì tầng thấp càng được ưu tiên rõ rệt
    # tang 1 luôn tốt nhất, tang càng cao càng bị phạt theo urgency
    penalty_per_level = 0.15 * urgency

    fit = 1.0 - penalty_per_level * max(tang - 1, 0)

    return float(np.clip(fit, 0.0, 1.0))


def rank_position(
    predictor_result: dict,
    product: dict,
    vitri: pd.DataFrame,
    tonkho: pd.DataFrame,
    cham: pd.DataFrame,
    top_k: int = 5,
    weights: dict = None,
    target_vi_tri_type_id: int = 2,
    # 2 = Reserve (mặc định, putaway hàng mới)
    # 1 = Primary (dùng cho module gợi ý châm hàng sau này)
    # 4 = Bãi Pick hàng (dùng cho module gợi ý pick sau này)
):
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    kho_id = product["kho_id"]
    san_pham_id = product["auto_id"]
    _ = cham

    required_position_cols = {
        "auto_id", "kho_id", "day_ke_id", "tang", "vi_tri_type_id"
    }
    missing = required_position_cols.difference(vitri.columns)
    if missing:
        raise ValueError(f"Thiếu cột vị trí: {sorted(missing)}")

    # Hard constraints come before scoring. A model must never make an
    # inactive/deleted/wrong-area location feasible.
    candidates = vitri[
        vitri["kho_id"].eq(kho_id)
        & vitri["vi_tri_type_id"].eq(target_vi_tri_type_id)
    ].copy()
    if "deleted" in candidates:
        candidates = candidates[candidates["deleted"].fillna(0).eq(0)]
    if "trang_thai_id" in candidates:
        candidates = candidates[candidates["trang_thai_id"].fillna(1).eq(1)]
    if candidates.empty:
        return pd.DataFrame()

    stock = tonkho.copy()
    if "kho_id" in stock:
        stock = stock[stock["kho_id"].eq(kho_id)]
    if "deleted" in stock:
        stock = stock[stock["deleted"].fillna(0).eq(0)]

    # Use net quantity instead of treating every historical stock row as
    # occupied. This removes ghost occupancy created by fully-issued LPNs.
    inbound = [c for c in ("sl_nhap_chan", "sl_nhap_le", "sl_nhap_all_special") if c in stock]
    outbound = [c for c in ("sl_xuat_chan", "sl_xuat_le", "sl_xuat_all_special") if c in stock]
    adjustments = [c for c in ("sl_dc_chan", "sl_dc_le", "sl_dc_all_special") if c in stock]
    if inbound or outbound or adjustments:
        stock["_net_qty"] = 0.0
        for col in inbound + adjustments:
            stock["_net_qty"] += pd.to_numeric(stock[col], errors="coerce").fillna(0)
        for col in outbound:
            stock["_net_qty"] -= pd.to_numeric(stock[col], errors="coerce").fillna(0)
        active_stock = stock[stock["_net_qty"] > 0].copy()
    else:
        active_stock = stock.copy()

    occupancy = (
        active_stock.groupby("vi_tri_id")["san_pham_id"]
        .agg(lambda values: tuple(pd.unique(values.dropna())))
        .rename("sku_set")
    )
    candidates = candidates.merge(occupancy, left_on="auto_id", right_index=True, how="left")
    candidates["sku_set"] = candidates["sku_set"].apply(
        lambda value: value if isinstance(value, tuple) else tuple()
    )
    candidates["empty"] = candidates["sku_set"].str.len().eq(0)
    candidates["same_product"] = candidates["sku_set"].apply(
        lambda values: bool(values) and all(value == san_pham_id for value in values)
    )
    candidates["other_product"] = ~(candidates["empty"] | candidates["same_product"])
    candidates = candidates[~candidates["other_product"]].copy()
    if candidates.empty:
        return pd.DataFrame()

    day_prediction = predictor_result["day_prediction"].set_index("day_ke_id")["probability"]
    tang_prediction = predictor_result["tang_prediction"]
    pair_probability = tang_prediction.copy()
    pair_probability["ai_raw"] = (
        0.6 * pair_probability["day_probability"]
        + 0.4 * pair_probability["probability"]
    )
    pair_probability = pair_probability.set_index(["day_ke_id", "tang"])["ai_raw"]

    candidates["day_probability"] = candidates["day_ke_id"].map(day_prediction).fillna(0.0)
    candidate_index = pd.MultiIndex.from_frame(candidates[["day_ke_id", "tang"]])
    candidates["ai_raw"] = pair_probability.reindex(candidate_index).fillna(0.0).to_numpy()
    candidates = candidates[candidates["ai_raw"] > 0].copy()
    if candidates.empty:
        return pd.DataFrame()

    # Capacity is calculated from actual occupied GW/CBM where available.
    used = active_stock.groupby("vi_tri_id").agg(
        used_gw=("gw", "sum") if "gw" in active_stock else ("san_pham_id", "size"),
        used_cbm=("cbm", "sum") if "cbm" in active_stock else ("san_pham_id", "size"),
    )
    if "gw" not in active_stock:
        used["used_gw"] = 0.0
    if "cbm" not in active_stock:
        used["used_cbm"] = 0.0
    candidates = candidates.merge(used, left_on="auto_id", right_index=True, how="left")
    candidates[["used_gw", "used_cbm"]] = candidates[["used_gw", "used_cbm"]].fillna(0.0)

    quantity = max(float(product.get("tong_nhap", 1) or 1), 1.0)
    unit_gw = max(float(product.get("gw_san_pham", 0) or 0), 0.0)
    unit_cbm = max(float(product.get("cbm_san_pham", 0) or 0), 0.0)
    required_gw, required_cbm = unit_gw * quantity, unit_cbm * quantity

    def capacity_fit(row):
        ratios = []
        if row.get("gw_max", 0) > 0 and unit_gw > 0:
            available = max(row["gw_max"] - row["used_gw"], 0.0)
            if available + 1e-9 < unit_gw:
                return 0.0
            ratios.append(min(available / max(required_gw, unit_gw), 1.0))
        if row.get("cbm_max", 0) > 0 and unit_cbm > 0:
            available = max(row["cbm_max"] - row["used_cbm"], 0.0)
            if available + 1e-9 < unit_cbm:
                return 0.0
            ratios.append(min(available / max(required_cbm, unit_cbm), 1.0))
        return min(ratios) if ratios else 0.5

    candidates["capacity_fit"] = candidates.apply(capacity_fit, axis=1)
    candidates = candidates[candidates["capacity_fit"] > 0].copy()
    if candidates.empty:
        return pd.DataFrame()

    # Prefer nearby slots of the same SKU. For a new SKU, use a stable
    # lower-sequence accessibility prior instead of CSV row order.
    seq = pd.to_numeric(candidates.get("vi_tri_seq_id", 0), errors="coerce").fillna(0)
    if "ma_so_vi_tri" in candidates:
        # Some warehouses store vi_tri_seq_id=0. Derive a stable physical
        # order from the location code so tied slots are not chosen by CSV
        # row order (for example N02265 -> 2265).
        code_seq = pd.to_numeric(
            candidates["ma_so_vi_tri"].astype(str).str.replace(r"\D", "", regex=True),
            errors="coerce",
        ).fillna(0)
        seq = seq.where(seq > 0, code_seq)
    candidates["_sequence"] = seq
    same_locations = candidates[candidates["same_product"]]
    same_seq_by_day = same_locations.groupby("day_ke_id")["_sequence"].median()
    nearest = (seq - candidates["day_ke_id"].map(same_seq_by_day)).abs()
    candidates["proximity_raw"] = 1.0 / (1.0 + nearest.fillna(seq))
    candidates["accessibility_raw"] = 1.0 / (1.0 + seq.clip(lower=0))

    candidates["physical_fit_raw"] = candidates["tang"].apply(
        lambda level: _physical_fit(level, unit_gw, unit_cbm, product.get("so_ngay_su_dung", 0))
    )
    active_ids = set(active_stock["vi_tri_id"].dropna())
    day_slots = candidates.groupby("day_ke_id")["auto_id"].nunique()
    day_used = candidates.assign(_used=candidates["auto_id"].isin(active_ids)).groupby("day_ke_id")["_used"].sum()
    candidates["day_load"] = candidates["day_ke_id"].map(day_used.div(day_slots).fillna(0))

    result = candidates

    # =====================================================
    # Chuẩn hóa min-max TRÊN TOÀN BỘ candidate của SKU này
    # -> mỗi thành phần thực sự trải rộng [0,1] thay vì bị nén
    # vào một khoảng hẹp (vd day_prob top-5 thường lệch nhau rất ít)
    # =====================================================

    def _minmax(series: pd.Series) -> pd.Series:
        lo, hi = series.min(), series.max()
        if hi - lo < 1e-9:
            return pd.Series(0.5, index=series.index)
        return (series - lo) / (hi - lo)

    result["ai_fit"] = _minmax(result["ai_raw"])

    # congestion: dãy càng tải nhiều càng nên bị trừ điểm
    # -> đảo dấu sau khi normalize để dùng chung công thức cộng dồn
    result["congestion_fit"] = 1.0 - _minmax(result["day_load"])

    result["proximity_fit"] = _minmax(result["proximity_raw"])
    result["accessibility_fit"] = _minmax(result["accessibility_raw"])

    # =====================================================
    # Điểm cuối cùng: tổng có trọng số, mọi thành phần đều [0,1]
    # =====================================================

    result["score"] = (
        weights["same_product"] * result["same_product"].astype(float)
        + weights["empty"] * result["empty"].astype(float)
        + weights["ai_probability"] * result["ai_fit"]
        + weights["physical_fit"] * result["physical_fit_raw"]
        + weights["congestion"] * result["congestion_fit"]
        + weights["capacity"] * result["capacity_fit"]
        + weights["proximity"] * result["proximity_fit"]
        + weights["accessibility"] * result["accessibility_fit"]
    )

    # =====================================================
    # Trùng vị trí
    # =====================================================

    result = (
        result
        .sort_values(
            ["score", "day_probability", "day_ke_id", "tang", "_sequence", "auto_id"],
            ascending=[False, False, True, True, True, True],
            kind="mergesort",
        )
        .drop_duplicates(
            subset="auto_id"
        )
    )

    # =====================================================
    # Top K
    # =====================================================

    return result.head(top_k)


import numpy as np
import pandas as pd

try:
    from .warehouse_graph import WarehouseGraph
except ImportError:  # Support running src/model/test.py directly.
    from warehouse_graph import WarehouseGraph



# Trọng số scoring — TẤT CẢ thành phần đều nằm trong [0,1] trước
# Tinh chỉnh ở đây, không cần sửa logic bên dưới.


DEFAULT_WEIGHTS = {
    "same_product": 0.15,
    "empty": 0.05,
    "ai_probability": 0.20,
    "physical_fit": 0.08,
    "congestion": 0.05,
    "capacity": 0.17,
    "proximity": 0.10,
    "accessibility": 0.12,
    "outbound_distance": 0.08,
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
    distance_matrix: pd.DataFrame = None,
    warehouse_graph: WarehouseGraph = None,
    # 2 = Reserve (mặc định, putaway hàng mới)
    # 1 = Primary (dùng cho module gợi ý châm hàng sau này)
    # 4 = Bãi Pick hàng (dùng cho module gợi ý pick sau này)
):
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
        feature = predictor_result.get("feature", {})
        abc_score = float(feature.get("abc_score", 1) or 1)
        velocity = float(np.clip((abc_score - 1.0) / 2.0, 0.0, 1.0))
        # Fast-moving A items pay more attention to the outbound route;
        # slow C items favor the inbound putaway route. Their combined
        # contribution stays constant, keeping scores comparable.
        weights["outbound_distance"] = 0.04 + 0.06 * velocity
        weights["accessibility"] = 0.20 - weights["outbound_distance"]
    else:
        weights = {**DEFAULT_WEIGHTS, **weights}
    kho_id = product["kho_id"]
    san_pham_id = product["auto_id"]
    _ = cham

    required_position_cols = {
        "auto_id", "kho_id", "day_ke_id", "tang", "vi_tri_type_id"
    }
    missing = required_position_cols.difference(vitri.columns)
    if missing:
        raise ValueError(f"Thiếu cột vị trí: {sorted(missing)}")

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

    if warehouse_graph is None:
        warehouse_graph = WarehouseGraph.from_positions(vitri, kho_id=kho_id)
    if distance_matrix is None:
        distance_matrix = warehouse_graph.distance_matrix()
    candidates = candidates.merge(distance_matrix, on="auto_id", how="left")

    # Prefer locations close to an existing Reserve slot of the same SKU.
    same_sku_location_ids = active_stock.loc[
        active_stock["san_pham_id"].eq(san_pham_id), "vi_tri_id"
    ].dropna().unique()
    graph_proximity = warehouse_graph.distances_from_locations(same_sku_location_ids)
    candidates["same_sku_distance_m"] = candidates["auto_id"].map(graph_proximity)

    seq = pd.to_numeric(candidates.get("vi_tri_seq_id", 0), errors="coerce").fillna(0)
    if "ma_so_vi_tri" in candidates:
        code_seq = pd.to_numeric(
            candidates["ma_so_vi_tri"].astype(str).str.replace(r"\D", "", regex=True),
            errors="coerce",
        ).fillna(0)
        seq = seq.where(seq > 0, code_seq)
    candidates["_sequence"] = seq

    candidates["physical_fit_raw"] = candidates["tang"].apply(
        lambda level: _physical_fit(level, unit_gw, unit_cbm, product.get("so_ngay_su_dung", 0))
    )
    active_ids = set(active_stock["vi_tri_id"].dropna())
    day_slots = candidates.groupby("day_ke_id")["auto_id"].nunique()
    day_used = candidates.assign(_used=candidates["auto_id"].isin(active_ids)).groupby("day_ke_id")["_used"].sum()
    candidates["day_load"] = candidates["day_ke_id"].map(day_used.div(day_slots).fillna(0))

    result = candidates

    # Chuẩn hóa min-max TRÊN TOÀN BỘ candidate của SKU này

    def _minmax(series: pd.Series) -> pd.Series:
        lo, hi = series.min(), series.max()
        if hi - lo < 1e-9:
            return pd.Series(0.5, index=series.index)
        return (series - lo) / (hi - lo)

    result["ai_fit"] = _minmax(result["ai_raw"])

    # congestion: dãy càng tải nhiều càng nên bị trừ điểm
    #  đảo dấu sau khi normalize để dùng chung công thức cộng dồn
    result["congestion_fit"] = 1.0 - _minmax(result["day_load"])

    def _distance_fit(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
        if numeric.notna().sum() == 0:
            return pd.Series(0.5, index=series.index)
        numeric = numeric.fillna(numeric.max())
        return 1.0 - _minmax(numeric)

    result["proximity_fit"] = _distance_fit(result["same_sku_distance_m"])
    result["accessibility_fit"] = _distance_fit(result["inbound_distance_m"])
    result["outbound_fit"] = _distance_fit(result["outbound_distance_m"])

    # Điểm cuối cùng: tổng có trọng số, mọi thành phần đều [0,1]

    result["score"] = (
        weights["same_product"] * result["same_product"].astype(float)
        + weights["empty"] * result["empty"].astype(float)
        + weights["ai_probability"] * result["ai_fit"]
        + weights["physical_fit"] * result["physical_fit_raw"]
        + weights["congestion"] * result["congestion_fit"]
        + weights["capacity"] * result["capacity_fit"]
        + weights["proximity"] * result["proximity_fit"]
        + weights["accessibility"] * result["accessibility_fit"]
        + weights["outbound_distance"] * result["outbound_fit"]
    )

    # Trùng vị trí

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

    # Top K

    return result.head(top_k)

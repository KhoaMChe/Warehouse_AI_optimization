def build_advanced_feature(feature):

    feature["inventory_turnover"] = (
        feature["tong_allocated"]
        / feature["tong_ton"]
    )

    feature["replenishment_ratio"] = (
        feature["tong_cham"]
        / feature["tong_xuat"]
    )

    feature["pick_density"] = (
        feature["tong_xuat"]
        / feature["so_vi_tri"]
    )

    return feature
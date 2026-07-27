import numpy as np
import pandas as pd

from .feature import (
    create_inventory_feature,
    create_outbound_feature,
    create_product_feature,
    create_replenishment_feature,
    create_temporal_feature,
)

def build_feature_table(
    sanpham,
    tonkho,
    nhapkho,
    xuatkho,
    cham,
    vitri
    
):

    product = create_product_feature(
        sanpham
    )

    inventory = create_inventory_feature(
        nhapkho,
        tonkho
    )

    outbound = create_outbound_feature(
        xuatkho
    )

    replenish = create_replenishment_feature(
        cham,
        outbound
    )

    temporal = create_temporal_feature(
        nhapkho
    )

    # location = build_location_feature(
    #     tonkho,
    #     vitri,
    # )

    feature = (
        tonkho[
            ["san_pham_id", "vi_tri_id", "kho_id"]
        ]
        .drop_duplicates()
    )
    feature = (
        feature
        .merge(product, on="san_pham_id", how="left")
        .merge(inventory, on="san_pham_id", how="left")
        .merge(outbound, on="san_pham_id", how="left")
        .merge(replenish, on="san_pham_id", how="left")
        .merge(temporal, on="san_pham_id", how="left")
        .merge(
            vitri[
                [
                    "auto_id",
                    "day_ke_id",
                    "ma_so_vi_tri",
                    "tang",
                    "vi_tri_type_id",
                ]
            ],
            left_on="vi_tri_id",
            right_on="auto_id",
            how="left",
        )
    )
    feature = feature.drop(columns="auto_id")
    feature["Vong_Quay_tonkho"] = (
        feature["tong_xuat"]
        / feature["ton_kho"]
    ).replace(np.inf,0).fillna(0)

    return feature



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
    cham
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

    feature = (
        product
        .merge(
            inventory,
            how="left"
        )
        .merge(
            outbound,
            how="left"
        )
        .merge(
            replenish,
            how="left"
        )
        .merge(
            temporal,
            how="left"
        )
    )

    feature = feature.fillna(0)

    feature["inventory_turnover"] = (
        feature["tong_xuat"]
        / feature["ton_kho"]
    ).replace(np.inf,0).fillna(0)

    return feature
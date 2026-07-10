# from .basic import build_basic_feature
# from .warehouse import build_location_feature
# from .temporal import build_temporal_feature
# from .advanced import build_advanced_feature


# def build_feature_table(
#     sanpham,
#     tonkho,
#     xuatkho,
#     cham,
#     vitri,
# ):

#     # Chuẩn hóa khóa chính
#     sanpham = sanpham.rename(columns={"auto_id": "san_pham_id"}).copy()
#     vitri = vitri.rename(columns={"auto_id": "vi_tri_id"}).copy()

#     feature = build_basic_feature(
#         sanpham,
#         tonkho,
#         xuatkho,
#         cham
#     )

#     feature = build_advanced_feature(feature)

#     location = build_location_feature(
#         tonkho,
#         vitri
#     )

#     return feature, location
from .inventory import create_inventory_feature
from .outbound import create_outbound_feature
from .replenishment import create_replenishment_feature
from .product import create_product_feature
from .temporal import create_temporal_feature


def build_feature_table(
    sanpham,
    tonkho,
    nhapkho,
    xuatkho,
    cham,
):

    inventory = create_inventory_feature(
        nhapkho,
        tonkho,
    )

    outbound = create_outbound_feature(
        xuatkho
    )

    replenishment = create_replenishment_feature(
        cham,
        outbound,
    )

    product = create_product_feature(
        sanpham
    )

    temporal = create_temporal_feature(
        nhapkho
    )

    feature = (
        product
        .merge(inventory, on="san_pham_id", how="left")
        .merge(outbound, on="san_pham_id", how="left")
        .merge(replenishment, on="san_pham_id", how="left")
        .merge(temporal, on="san_pham_id", how="left")
    )

    feature = feature.fillna(
        {
            "tong_nhap": 0,
            "tong_xuat": 0,
            "ton_kho": 0,
            "tan_suat_xuat": 0,
            "ti_le_cham_hang": 0,
            "abc_class": "C",
        }
    )

    return feature
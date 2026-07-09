from .basic import build_basic_feature
from .warehouse import build_location_feature
from .temporal import build_temporal_feature
from .advanced import build_advanced_feature


def build_feature_table(
    sanpham,
    tonkho,
    xuatkho,
    cham,
    vitri,
):

    # Chuẩn hóa khóa chính
    sanpham = sanpham.rename(columns={"auto_id": "san_pham_id"}).copy()
    vitri = vitri.rename(columns={"auto_id": "vi_tri_id"}).copy()

    feature = build_basic_feature(
        sanpham,
        tonkho,
        xuatkho,
        cham
    )

    feature = build_advanced_feature(feature)

    location = build_location_feature(
        tonkho,
        vitri
    )

    return feature, location
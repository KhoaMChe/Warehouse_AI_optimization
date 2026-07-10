def create_product_feature(sanpham):

    return (
        sanpham.rename(
            columns={"auto_id": "san_pham_id"}
        )[
            [
                "san_pham_id",
                "nganh_hang_id"
            ]
        ]
    )
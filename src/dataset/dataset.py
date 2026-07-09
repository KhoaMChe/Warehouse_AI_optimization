import pandas as pd


def build_warehouse_dataset(
    feature_table: pd.DataFrame,
    tonkho: pd.DataFrame,
):
    """
    Dataset dùng để train model dự đoán kho.
    """

    # =====================================
    # Kho chính của mỗi SKU
    # =====================================

    warehouse = (
        tonkho
        .groupby(
            ["san_pham_id", "kho_id"]
        )
        .agg(
            tong_ton=("sl_nhap_chan", "sum")
        )
        .reset_index()
    )

    warehouse = (
        warehouse
        .sort_values(
            ["san_pham_id", "tong_ton"],
            ascending=[True, False]
        )
        .drop_duplicates("san_pham_id")
    )

    warehouse = warehouse[
        ["san_pham_id", "kho_id"]
    ]

    # =====================================

    dataset = feature_table.merge(
        warehouse,
        on="san_pham_id",
        how="inner"
    )

    return dataset
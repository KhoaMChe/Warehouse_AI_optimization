import pandas as pd
import numpy as np


def create_replenishment_feature(cham, xuat_feature):

    rep = (
        cham
        .groupby("san_pham_id")
        .size()
        .rename("so_lan_cham")
        .reset_index()
    )

    rep = rep.merge(
        xuat_feature[
            ["san_pham_id", "tan_suat_xuat"]
        ],
        on="san_pham_id",
        how="left"
    )

    rep["ti_le_cham_hang"] = (
        rep["so_lan_cham"]
        / rep["tan_suat_xuat"]
    )

    rep["ti_le_cham_hang"] = (
        rep["ti_le_cham_hang"]
        .replace(np.inf, 0)
        .fillna(0)
    )

    return rep[
        [
            "san_pham_id",
            "ti_le_cham_hang"
        ]
    ]
import unittest

import pandas as pd

from src.model.ranking import rank_position


class SlottingRankingTests(unittest.TestCase):
    def setUp(self):
        self.positions = pd.DataFrame([
            {"auto_id": 1, "kho_id": 10, "day_ke_id": 100, "tang": 1,
             "vi_tri_type_id": 2, "vi_tri_seq_id": 10, "gw_max": 100,
             "cbm_max": 1000, "deleted": 0, "trang_thai_id": 1,
             "ma_so_vi_tri": "R-010"},
            {"auto_id": 2, "kho_id": 10, "day_ke_id": 100, "tang": 1,
             "vi_tri_type_id": 2, "vi_tri_seq_id": 2, "gw_max": 100,
             "cbm_max": 1000, "deleted": 0, "trang_thai_id": 1,
             "ma_so_vi_tri": "R-002"},
            {"auto_id": 3, "kho_id": 10, "day_ke_id": 100, "tang": 1,
             "vi_tri_type_id": 1, "vi_tri_seq_id": 1, "gw_max": 100,
             "cbm_max": 1000, "deleted": 0, "trang_thai_id": 1,
             "ma_so_vi_tri": "P-001"},
        ])
        self.stock = pd.DataFrame(columns=[
            "vi_tri_id", "san_pham_id", "kho_id", "deleted",
            "sl_nhap_chan", "sl_xuat_chan", "gw", "cbm",
        ])
        self.prediction = {
            "day_prediction": pd.DataFrame({"day_ke_id": [100], "probability": [.8]}),
            "tang_prediction": pd.DataFrame({
                "tang": [1], "probability": [.9], "day_ke_id": [100],
                "day_probability": [.8],
            }),
        }
        self.product = {
            "auto_id": 99, "kho_id": 10, "gw_san_pham": 5,
            "cbm_san_pham": 20, "so_ngay_su_dung": 300, "tong_nhap": 2,
        }

    def test_only_reserve_and_stable_sequence_order(self):
        result = rank_position(
            self.prediction, self.product, self.positions, self.stock,
            pd.DataFrame(), top_k=5,
        )
        self.assertTrue(result["vi_tri_type_id"].eq(2).all())
        self.assertEqual(result["auto_id"].tolist(), [2, 1])

    def test_location_without_one_unit_capacity_is_rejected(self):
        self.positions.loc[self.positions["auto_id"].eq(2), "cbm_max"] = 10
        result = rank_position(
            self.prediction, self.product, self.positions, self.stock,
            pd.DataFrame(), top_k=5,
        )
        self.assertNotIn(2, result["auto_id"].tolist())


if __name__ == "__main__":
    unittest.main()

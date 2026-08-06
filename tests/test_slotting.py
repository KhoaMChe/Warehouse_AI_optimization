import unittest

import pandas as pd

from src.model.ranking import rank_position
from src.model.warehouse_graph import WarehouseGraph, WarehouseGraphConfig


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


class WarehouseGraphTests(unittest.TestCase):
    def test_shortest_path_uses_cross_aisle_not_rack_crossing(self):
        positions = pd.DataFrame([
            {"auto_id": 1, "kho_id": 10, "day_ke_id": "A", "tang": 1,
             "vi_tri_seq_id": 1, "ma_so_vi_tri": "A-001", "deleted": 0},
            {"auto_id": 2, "kho_id": 10, "day_ke_id": "A", "tang": 1,
             "vi_tri_seq_id": 2, "ma_so_vi_tri": "A-002", "deleted": 0},
            {"auto_id": 3, "kho_id": 10, "day_ke_id": "B", "tang": 1,
             "vi_tri_seq_id": 1, "ma_so_vi_tri": "B-001", "deleted": 0},
            {"auto_id": 4, "kho_id": 10, "day_ke_id": "B", "tang": 1,
             "vi_tri_seq_id": 2, "ma_so_vi_tri": "B-002", "deleted": 0},
        ])
        config = WarehouseGraphConfig(
            rack_spacing_m=4.0,
            bay_spacing_m=1.2,
            include_top_cross_aisle=False,
        )
        graph = WarehouseGraph.from_positions(positions, kho_id=10, config=config)
        distance = graph.distances_from_locations([2])

        # 1.2 m down aisle A + 4 m cross-aisle + 1.2 m up aisle B.
        self.assertAlmostEqual(distance[4], 6.4)
        self.assertEqual(len(graph.gates["inbound"]), 7)
        self.assertEqual(len(graph.gates["outbound"]), 6)
        self.assertTrue(graph.distance_matrix()["inbound_distance_m"].notna().all())


if __name__ == "__main__":
    unittest.main()

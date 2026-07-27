from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "models"
class Predictor:
    """
    Predictor cho hệ thống Warehouse AI.

    Chức năng
    ---------
    - Load model theo kho
    - Load feature table
    - Sinh feature cho SKU cũ
    - Sinh feature cho SKU mới
    - Predict Day
    - Predict Tầng

    Ranking vị trí sẽ xử lý ở ranking.py
    """

    def __init__(
        self,
        feature_table: pd.DataFrame,
        model_root: str,
    ):

        self.feature_table = feature_table

        self.model_root = Path(model_root)

        self.day_model = None
        self.tang_model = None
        self.day_columns = None
        self.tang_columns = None
        self.loaded_kho = None
    # ==========================================================
    # Load model
    # ==========================================================

    def load_model(
        self,
        kho_id: int,
    ):

        # Nếu đã load kho này rồi thì bỏ qua
        if self.loaded_kho == kho_id:
            return
        
        folder = MODEL_DIR / str(kho_id) / "RandomForest"

        if not folder.exists():
            raise FileNotFoundError(
                f"Không tìm thấy model: {folder}"
            )

        self.day_model = joblib.load(
            folder / "day_ke_id.pkl"
        )

        self.tang_model = joblib.load(
            folder / "tang.pkl"
        )

        self.day_columns = joblib.load(
            folder / "day_ke_id_columns.pkl"
        )

        self.tang_columns = joblib.load(
            folder / "tang_columns.pkl"
        )

    # ==========================================================
    # Kiểm tra model
    # ==========================================================

    def _check_model(self):

        if self.day_model is None:
            raise RuntimeError(
                "Chưa load model."
            )

        if self.tang_model is None:
            raise RuntimeError(
                "Chưa load model."
            )

        if self.day_columns is None:
            raise RuntimeError("Missing day columns")

        if self.tang_columns is None:
            raise RuntimeError("Missing tang columns")

    # ==========================================================
    # SKU đã tồn tại ?
    # ==========================================================

    def sku_exists(
        self,
        san_pham_id: int,
    ) -> bool:

        return (
            san_pham_id
            in
            self.feature_table["san_pham_id"].values
        )

    # ==========================================================
    # Feature của SKU cũ
    # ==========================================================

    def get_old_feature(self, san_pham_id):

        feature = self.feature_table.query(
            "san_pham_id == @san_pham_id"
        )

        if feature.empty:
            raise ValueError(
                f"Không tìm thấy feature của SKU {san_pham_id}"
            )

        feature = feature.iloc[0].copy()

        drop_cols = [
            "san_pham_id",
            "vi_tri_id",
            "day_ke_id",
            "ma_so_vi_tri",
            "kho_id",
            "abc_class",
        ]

        feature = feature.drop(
            labels=[c for c in drop_cols if c in feature.index]
        )

        return feature

    # ==========================================================
    # Lấy dữ liệu cùng ngành
    # ==========================================================

    def get_same_category(
        self,
        nganh_hang_id: int,
    ) -> pd.DataFrame:

        same = (

            self.feature_table

            .query(
                "nganh_hang_id == @nganh_hang_id"
            )

        )

        if len(same) == 0:

            same = self.feature_table.copy()

        return same

    # ==========================================================
    # Sinh feature cho SKU mới
    # ==========================================================

    def build_new_feature(
        self,
        product: dict,
    ) -> pd.Series:

        same = self.get_same_category(
            product["nganh_hang_id"]
        )

        feature = {}

        # ==========================================
        # Thông tin sản phẩm do người dùng nhập
        # ==========================================

        feature["nganh_hang_id"] = product.get(
            "nganh_hang_id",
            0,
        )

        feature["gw_san_pham"] = product.get(
            "gw_san_pham",
            0,
        )

        feature["cbm_san_pham"] = product.get(
            "cbm_san_pham",
            0,
        )

        feature["so_ngay_su_dung"] = product.get(
            "so_ngay_su_dung",
            0,
        )

        # ==========================================
        # Feature lịch sử
        # ==========================================

        history_columns = [

            "tong_nhap",

            "ton_kho",

            "tong_xuat",

            "tan_suat_xuat",

            "abc_score",

            "ti_le_cham_hang",

            "shelf_life_days",

            "remaining_shelf_life_days",

            "inventory_age_days",

            "Vong_Quay_tonkho",

        ]

        for col in history_columns:

            if col in same.columns:

                feature[col] = (

                    same[col]

                    .mean()

                )

            else:

                feature[col] = 0

        # ==========================================
        # Các feature còn thiếu
        # ==========================================

        all_columns = list(
            set(self.day_columns) | set(self.tang_columns)
        )

        for col in all_columns:
            if col not in feature:
                feature[col] = 0

        feature = pd.Series(feature)

        feature = feature.reindex(all_columns).fillna(0)

        return feature

    # ==========================================================
    # Build feature
    # ==========================================================

    def build_feature(
        self,
        product: dict,
    ) -> pd.Series:

        self._check_model()

        san_pham_id = product["auto_id"]

        if self.sku_exists(
            san_pham_id
        ):

            feature = self.get_old_feature(
                san_pham_id
            )

        else:

            feature = self.build_new_feature(
                product
            )

        all_columns = list(
            set(self.day_columns) | set(self.tang_columns)
        )

        feature = (
            feature
            .reindex(all_columns)
            .fillna(0)
        )

        return feature

    # ==========================================================
    # Build nhiều SKU
    # ==========================================================

    def build_batch_feature(
        self,
        products: list,
    ) -> pd.DataFrame:

        rows = []

        for product in products:

            rows.append(

                self.build_feature(
                    product
                )

            )

        return pd.DataFrame(rows)

    # ==========================================================
    # Predict Day
    # ==========================================================

    def predict_day(
        self,
        feature: pd.Series,
        top_k: int = 5,
    ):

        X = (
            feature
            .reindex(self.day_columns)
            .fillna(0)
            .to_frame()
            .T
        )

        prob = self.day_model.predict_proba(X)[0]

        result = (
            pd.DataFrame(
                {
                    "day_ke_id": self.day_model.classes_,
                    "probability": prob,
                }
            )
            .sort_values(
                "probability",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        return result.head(top_k)

    # ==========================================================
    # Predict Tầng
    # ==========================================================

    def predict_tang(
        self,
        feature: pd.Series,
        top_k: int = 3,
    ):

        X = (
            feature
            .reindex(self.tang_columns)
            .fillna(0)
            .to_frame()
            .T
        )

        prob = self.tang_model.predict_proba(X)[0]

        result = (
            pd.DataFrame(
                {
                    "tang": self.tang_model.classes_,
                    "probability": prob,
                }
            )
            .sort_values(
                "probability",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        return result.head(top_k)

    # ==========================================================
    # Predict 1 SKU
    # ==========================================================

    def predict(
        self,
        product: dict,
        top_day: int = 5,
        top_tang: int = 3,
    ):

        # Build feature
        feature = self.build_feature(product)

        # Predict dãy
        day = self.predict_day(
            feature,
            top_day,
        )

        # Dùng Day Top 1 làm input cho model tầng
        feature["day_ke_id"] = (
            day.iloc[0]["day_ke_id"]
        )

        # Predict tầng
        tang = self.predict_tang(
            feature,
            top_tang,
        )

        return {

            "feature": feature,

            "day_prediction": day,

            "tang_prediction": tang,

        }

    # ==========================================================
    # Predict nhiều SKU
    # ==========================================================

    def predict_batch(
        self,
        products: list,
        top_day: int = 5,
        top_tang: int = 3,
    ) -> list:

        results = []

        for product in products:

            results.append(

                self.predict(
                    product,
                    top_day=top_day,
                    top_tang=top_tang,
                )

            )

        return results

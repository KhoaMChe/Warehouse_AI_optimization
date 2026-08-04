# from pathlib import Path

# import joblib
# import numpy as np
# import pandas as pd
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parents[2]
# MODEL_DIR = BASE_DIR / "models"
# class Predictor:
#     """
#     Predictor cho hệ thống Warehouse AI.

#     Chức năng
#     ---------
#     - Load model theo kho
#     - Load feature table
#     - Sinh feature cho SKU cũ
#     - Sinh feature cho SKU mới
#     - Predict Day
#     - Predict Tầng

#     Ranking vị trí sẽ xử lý ở ranking.py
#     """

#     def __init__(
#         self,
#         feature_table: pd.DataFrame,
#         model_root: str,
#     ):

#         self.feature_table = feature_table

#         self.model_root = Path(model_root)

#         self.day_model = None
#         self.tang_model = None
#         self.day_columns = None
#         self.tang_columns = None
#         self.loaded_kho = None
#     # ==========================================================
#     # Load model
#     # ==========================================================

#     def load_model(
#         self,
#         kho_id: int,
#     ):

#         # Nếu đã load kho này rồi thì bỏ qua
#         if self.loaded_kho == kho_id:
#             return
        
#         folder = MODEL_DIR / str(kho_id) / "RandomForest"

#         if not folder.exists():
#             raise FileNotFoundError(
#                 f"Không tìm thấy model: {folder}"
#             )

#         self.day_model = joblib.load(
#             folder / "day_ke_id.pkl"
#         )

#         self.tang_model = joblib.load(
#             folder / "tang.pkl"
#         )

#         self.day_columns = joblib.load(
#             folder / "day_ke_id_columns.pkl"
#         )

#         self.tang_columns = joblib.load(
#             folder / "tang_columns.pkl"
#         )

#     # ==========================================================
#     # Kiểm tra model
#     # ==========================================================

#     def _check_model(self):

#         if self.day_model is None:
#             raise RuntimeError(
#                 "Chưa load model."
#             )

#         if self.tang_model is None:
#             raise RuntimeError(
#                 "Chưa load model."
#             )

#         if self.day_columns is None:
#             raise RuntimeError("Missing day columns")

#         if self.tang_columns is None:
#             raise RuntimeError("Missing tang columns")

#     # ==========================================================
#     # SKU đã tồn tại ?
#     # ==========================================================

#     def sku_exists(
#         self,
#         san_pham_id: int,
#     ) -> bool:

#         return (
#             san_pham_id
#             in
#             self.feature_table["san_pham_id"].values
#         )

#     # ==========================================================
#     # Feature của SKU cũ
#     # ==========================================================

#     def get_old_feature(self, san_pham_id):

#         feature = self.feature_table.query(
#             "san_pham_id == @san_pham_id"
#         )

#         if feature.empty:
#             raise ValueError(
#                 f"Không tìm thấy feature của SKU {san_pham_id}"
#             )

#         feature = feature.iloc[0].copy()

#         drop_cols = [
#             "san_pham_id",
#             "vi_tri_id",
#             "day_ke_id",
#             "ma_so_vi_tri",
#             "kho_id",
#             "abc_class",
#         ]

#         feature = feature.drop(
#             labels=[c for c in drop_cols if c in feature.index]
#         )

#         return feature

#     # ==========================================================
#     # Lấy dữ liệu cùng ngành
#     # ==========================================================

#     def get_same_category(
#         self,
#         nganh_hang_id: int,
#     ) -> pd.DataFrame:

#         same = (

#             self.feature_table

#             .query(
#                 "nganh_hang_id == @nganh_hang_id"
#             )

#         )

#         if len(same) == 0:

#             same = self.feature_table.copy()

#         return same

#     # ==========================================================
#     # Sinh feature cho SKU mới
#     # ==========================================================

#     def build_new_feature(
#         self,
#         product: dict,
#     ) -> pd.Series:

#         same = self.get_same_category(
#             product["nganh_hang_id"]
#         )

#         feature = {}

#         # ==========================================
#         # Thông tin sản phẩm do người dùng nhập
#         # ==========================================

#         feature["nganh_hang_id"] = product.get(
#             "nganh_hang_id",
#             0,
#         )

#         feature["gw_san_pham"] = product.get(
#             "gw_san_pham",
#             0,
#         )

#         feature["cbm_san_pham"] = product.get(
#             "cbm_san_pham",
#             0,
#         )

#         feature["so_ngay_su_dung"] = product.get(
#             "so_ngay_su_dung",
#             0,
#         )

#         # ==========================================
#         # Feature lịch sử
#         # ==========================================

#         history_columns = [

#             "tong_nhap",

#             "ton_kho",

#             "tong_xuat",

#             "tan_suat_xuat",

#             "abc_score",

#             "ti_le_cham_hang",

#             "shelf_life_days",

#             "remaining_shelf_life_days",

#             "inventory_age_days",

#             "Vong_Quay_tonkho",

#         ]

#         for col in history_columns:

#             if col in same.columns:

#                 feature[col] = (

#                     same[col]

#                     .mean()

#                 )

#             else:

#                 feature[col] = 0

#         # ==========================================
#         # Các feature còn thiếu
#         # ==========================================

#         all_columns = list(
#             set(self.day_columns) | set(self.tang_columns)
#         )

#         for col in all_columns:
#             if col not in feature:
#                 feature[col] = 0

#         feature = pd.Series(feature)

#         feature = feature.reindex(all_columns).fillna(0)

#         return feature

#     # ==========================================================
#     # Build feature
#     # ==========================================================

#     def build_feature(
#         self,
#         product: dict,
#     ) -> pd.Series:

#         self._check_model()

#         san_pham_id = product["auto_id"]

#         if self.sku_exists(
#             san_pham_id
#         ):

#             feature = self.get_old_feature(
#                 san_pham_id
#             )

#         else:

#             feature = self.build_new_feature(
#                 product
#             )

#         all_columns = list(
#             set(self.day_columns) | set(self.tang_columns)
#         )

#         feature = (
#             feature
#             .reindex(all_columns)
#             .fillna(0)
#         )

#         return feature

#     # ==========================================================
#     # Build nhiều SKU
#     # ==========================================================

#     def build_batch_feature(
#         self,
#         products: list,
#     ) -> pd.DataFrame:

#         rows = []

#         for product in products:

#             rows.append(

#                 self.build_feature(
#                     product
#                 )

#             )

#         return pd.DataFrame(rows)

#     # ==========================================================
#     # Predict Day
#     # ==========================================================

#     def predict_day(
#         self,
#         feature: pd.Series,
#         top_k: int = 5,
#     ):

#         X = (
#             feature
#             .reindex(self.day_columns)
#             .fillna(0)
#             .to_frame()
#             .T
#         )

#         prob = self.day_model.predict_proba(X)[0]

#         result = (
#             pd.DataFrame(
#                 {
#                     "day_ke_id": self.day_model.classes_,
#                     "probability": prob,
#                 }
#             )
#             .sort_values(
#                 "probability",
#                 ascending=False,
#             )
#             .reset_index(drop=True)
#         )

#         return result.head(top_k)

#     # ==========================================================
#     # Predict Tầng
#     # ==========================================================

#     def predict_tang(
#         self,
#         feature: pd.Series,
#         top_k: int = 3,
#     ):

#         X = (
#             feature
#             .reindex(self.tang_columns)
#             .fillna(0)
#             .to_frame()
#             .T
#         )

#         prob = self.tang_model.predict_proba(X)[0]

#         result = (
#             pd.DataFrame(
#                 {
#                     "tang": self.tang_model.classes_,
#                     "probability": prob,
#                 }
#             )
#             .sort_values(
#                 "probability",
#                 ascending=False,
#             )
#             .reset_index(drop=True)
#         )

#         return result.head(top_k)

#     # ==========================================================
#     # Predict 1 SKU
#     # ==========================================================

#     def predict(
#         self,
#         product: dict,
#         top_day: int = 5,
#         top_tang: int = 3,
#     ):

#         # Build feature
#         feature = self.build_feature(product)

#         # Predict dãy
#         day = self.predict_day(
#             feature,
#             top_day,
#         )

#         # Dùng Day Top 1 làm input cho model tầng
#         feature["day_ke_id"] = (
#             day.iloc[0]["day_ke_id"]
#         )

#         # Predict tầng
#         tang = self.predict_tang(
#             feature,
#             top_tang,
#         )

#         return {

#             "feature": feature,

#             "day_prediction": day,

#             "tang_prediction": tang,

#         }

#     # ==========================================================
#     # Predict nhiều SKU
#     # ==========================================================

#     def predict_batch(
#         self,
#         products: list,
#         top_day: int = 5,
#         top_tang: int = 3,
#     ) -> list:

#         results = []

#         for product in products:

#             results.append(

#                 self.predict(
#                     product,
#                     top_day=top_day,
#                     top_tang=top_tang,
#                 )

#             )

#         return results
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
        
        folder = self.model_root / str(kho_id) / "RandomForest"

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

        # Mark the model only after every artifact was loaded successfully.
        self.loaded_kho = kho_id

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

    def get_old_feature(self, san_pham_id, target_vi_tri_type_id=None):

        feature = self.feature_table.query(
            "san_pham_id == @san_pham_id"
        )

        if feature.empty:
            raise ValueError(
                f"Không tìm thấy feature của SKU {san_pham_id}"
            )

        # ==========================================================
        # BUG FIX: 1 SKU có thể có nhiều dòng feature, mỗi dòng ứng
        # với 1 vị trí lịch sử khác nhau (Primary/Reserve/Bãi Put...).
        # iloc[0] lấy ĐẠI dòng đầu tiên -> vi_tri_type_id đi kèm hoàn
        # toàn ngẫu nhiên, không liên quan gì đến loại vị trí đang
        # muốn dự đoán (vd Reserve). Vì vi_tri_type_id LÀ 1 feature
        # được model học (không nằm trong drop_cols khi train), việc
        # đưa sai giá trị này khiến model trả lời cho ĐÚNG câu hỏi
        # SAI ("SKU này nên ở đâu nói chung theo dòng ngẫu nhiên đó"
        # thay vì "SKU này nên ở Reserve nào").
        #
        # Các cột đặc trưng sản phẩm (tong_nhap, ton_kho, abc_score...)
        # giống hệt nhau ở mọi dòng của cùng 1 SKU nên lấy dòng nào
        # cũng an toàn -- CHỈ RIÊNG vi_tri_type_id là cần ép lại đúng.
        # ==========================================================

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

        if target_vi_tri_type_id is not None and "vi_tri_type_id" in feature.index:
            feature["vi_tri_type_id"] = target_vi_tri_type_id

        return feature

    # ==========================================================
    # Lấy dữ liệu cùng ngành
    # ==========================================================

    def get_same_category(
        self,
        nganh_hang_id: int,
    ) -> pd.DataFrame:

        same = self.feature_table.query("nganh_hang_id == @nganh_hang_id")

        # Product statistics and location patterns are warehouse-specific.
        if self.loaded_kho is not None and "kho_id" in same.columns:
            same = same[same["kho_id"] == self.loaded_kho]

        if len(same) == 0:

            same = self.feature_table.copy()
            if self.loaded_kho is not None and "kho_id" in same.columns:
                same = same[same["kho_id"] == self.loaded_kho]

        return same

    # ==========================================================
    # Sinh feature cho SKU mới
    # ==========================================================

    def build_new_feature(
        self,
        product: dict,
        target_vi_tri_type_id=2,
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

        # ==========================================================
        # BUG FIX: trước đây vi_tri_type_id không được set ở đây,
        # nên bị mặc định về 0 ở bước "feature còn thiếu" bên dưới.
        # 0 KHÔNG phải giá trị hợp lệ (loại vị trí thật là 1-16),
        # nên model gặp 1 category chưa từng thấy khi train -> dự
        # đoán không đáng tin cậy cho SKU mới hoàn toàn.
        # ==========================================================

        if target_vi_tri_type_id is not None:
            feature["vi_tri_type_id"] = target_vi_tri_type_id

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
        target_vi_tri_type_id=2,
    ) -> pd.Series:

        self._check_model()

        san_pham_id = product["auto_id"]

        if self.sku_exists(
            san_pham_id
        ):

            feature = self.get_old_feature(
                san_pham_id,
                target_vi_tri_type_id=target_vi_tri_type_id,
            )

        else:

            feature = self.build_new_feature(
                product,
                target_vi_tri_type_id=target_vi_tri_type_id,
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

    def predict_day_for_warehouse(
        self,
        feature: pd.Series,
        top_k: int = 5,
        target_vi_tri_type_id: int = 2,
    ):
        """Predict aisle without borrowing an arbitrary historical floor.

        Legacy models include ``tang`` in the aisle features. At putaway time
        that value is unknown, so we marginalize probabilities over the real
        Reserve-floor distribution of the loaded warehouse.
        """
        if "tang" not in self.day_columns:
            return self.predict_day(feature, top_k)

        context = self.feature_table
        if "kho_id" in context.columns and self.loaded_kho is not None:
            context = context[context["kho_id"].eq(self.loaded_kho)]
        if "vi_tri_type_id" in context.columns:
            context = context[context["vi_tri_type_id"].eq(target_vi_tri_type_id)]

        levels = pd.to_numeric(context.get("tang", pd.Series(dtype=float)), errors="coerce")
        distribution = levels[levels > 0].value_counts(normalize=True)
        if distribution.empty:
            return self.predict_day(feature, top_k)

        probability = np.zeros(len(self.day_model.classes_), dtype=float)
        for level, weight in distribution.items():
            feature_for_level = feature.copy()
            feature_for_level["tang"] = level
            X = feature_for_level.reindex(self.day_columns).fillna(0).to_frame().T
            probability += float(weight) * self.day_model.predict_proba(X)[0]

        result = pd.DataFrame({
            "day_ke_id": self.day_model.classes_,
            "probability": probability,
        })
        return result.sort_values("probability", ascending=False).head(top_k).reset_index(drop=True)

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
        target_vi_tri_type_id=2,
        # vd 2 = Reserve cho module Putaway. Ép feature vi_tri_type_id
        # về đúng loại này trước khi predict, thay vì để giá trị
        # ngẫu nhiên/lịch sử lẫn lộn (xem ghi chú trong get_old_feature).
    ):

        # Build feature
        feature = self.build_feature(
            product,
            target_vi_tri_type_id=target_vi_tri_type_id,
        )

        # Predict dãy (top K)
        day = self.predict_day_for_warehouse(
            feature,
            top_day,
            target_vi_tri_type_id=target_vi_tri_type_id,
        )

        # ==========================================================
        # BUG FIX: trước đây chỉ dùng day top-1 để predict tầng,
        # rồi ranking.py lại loop qua cả 5 dãy với CÙNG 1 bộ tầng đó
        # -> tầng bị "vay mượn" sai ngữ cảnh cho 4/5 dãy còn lại.
        #
        # Sửa: predict tầng RIÊNG cho từng dãy trong top_day, để mỗi
        # cặp (dãy, tầng) đều phản ánh đúng xác suất theo ngữ cảnh
        # của dãy đó.
        # ==========================================================

        tang_frames = []

        for _, day_row in day.iterrows():

            day_ke_id = day_row["day_ke_id"]
            day_prob = day_row["probability"]

            feature_for_day = feature.copy()
            feature_for_day["day_ke_id"] = day_ke_id

            tang_for_day = self.predict_tang(
                feature_for_day,
                top_tang,
            )

            tang_for_day["day_ke_id"] = day_ke_id
            tang_for_day["day_probability"] = day_prob

            tang_frames.append(tang_for_day)

        tang = (
            pd.concat(tang_frames, ignore_index=True)
            if tang_frames
            else pd.DataFrame(columns=["tang", "probability", "day_ke_id", "day_probability"])
        )

        return {

            "feature": feature,

            "day_prediction": day,

            # Giờ có cột day_ke_id + day_probability đi kèm,
            # mỗi hàng tầng đã gắn đúng dãy sinh ra nó.
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
        target_vi_tri_type_id=2,
    ) -> list:

        results = []

        for product in products:

            results.append(

                self.predict(
                    product,
                    top_day=top_day,
                    top_tang=top_tang,
                    target_vi_tri_type_id=target_vi_tri_type_id,
                )

            )

        return results

from pathlib import Path

import pandas as pd
import streamlit as st

from src.model.predictor import Predictor
from src.model.ranking import rank_position

# ==========================================================
# Config
# ==========================================================

st.set_page_config(
    page_title="Warehouse AI",
    page_icon="📦",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# Cache
# ==========================================================

@st.cache_data
def load_data():

    feature_table = pd.read_csv(
        BASE_DIR / "./data/process/classic_feature.csv",
        low_memory=False,
    )

    vitri = pd.read_csv(
        BASE_DIR / "./data/clean/dm_vi_tri_clean.csv",
        low_memory=False,
    )

    tonkho = pd.read_csv(
        BASE_DIR / "./data/clean/xnk_ton_kho_clean.csv",
        low_memory=False,
    )

    cham = pd.read_csv(
        BASE_DIR / "./data/clean/log_cham_hang.csv",
        low_memory=False,
    )

    return feature_table, vitri, tonkho, cham


@st.cache_resource
def load_predictor(feature_table):

    predictor = Predictor(
        feature_table=feature_table,
        model_root=BASE_DIR / "./models",
    )

    return predictor


feature_table, vitri, tonkho, cham = load_data()

predictor = load_predictor(feature_table)

# ==========================================================
# Header
# ==========================================================

st.title("📦 Warehouse AI Slotting")

st.write(
    "AI gợi ý vị trí lưu trữ hàng hóa."
)

# ==========================================================
# Kho
# ==========================================================

warehouse = st.selectbox(
    "Kho",
    [
        12473657,
        12630825,
        12630830,
    ],
)

predictor.load_model(warehouse)

# ==========================================================
# Form
# ==========================================================

with st.form("predict"):

    col1, col2 = st.columns(2)

    with col1:

        auto_id = st.number_input(
            "SKU",
            value=99999999,
        )

        nganh_hang_id = st.number_input(
            "Ngành hàng",
            value=18,
        )

        gw = st.number_input(
            "GW",
            value=1.5,
        )

        cbm = st.number_input(
            "CBM",
            value=0.006,
        )

    with col2:

        shelf = st.number_input(
            "Số ngày sử dụng",
            value=365,
        )

        quantity = st.number_input(
            "Số lượng nhập",
            value=300,
        )

    submit = st.form_submit_button(
        "Gợi ý vị trí"
    )

# ==========================================================
# Predict
# ==========================================================

if submit:

    product = {

        "auto_id": auto_id,

        "kho_id": warehouse,

        "nganh_hang_id": nganh_hang_id,

        "gw_san_pham": gw,

        "cbm_san_pham": cbm,

        "so_ngay_su_dung": shelf,

        "tong_nhap": quantity,

    }

    result = predictor.predict(product)

    ranking = rank_position(

        predictor_result=result,

        product=product,

        vitri=vitri,

        tonkho=tonkho,

        cham=cham,

        top_k=5,

    )

    # ======================================================
    # Day
    # ======================================================

    st.subheader("Top Day")

    st.dataframe(
        result["day_prediction"],
        use_container_width=True,
    )

    # ======================================================
    # Tang
    # ======================================================

    st.subheader("Top Tầng")

    st.dataframe(
        result["tang_prediction"],
        use_container_width=True,
    )

    # ======================================================
    # Position
    # ======================================================

    st.subheader("Top 5 vị trí")

    if ranking.empty:

        st.warning(
            "Không tìm thấy vị trí phù hợp."
        )

    else:

        st.dataframe(

            ranking[
                [
                    "ma_so_vi_tri",
                    "day_ke_id",
                    "tang",
                    "score",
                    "same_product",
                    "empty",
                ]
            ],

            use_container_width=True,

        )
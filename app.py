from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.model.predictor import Predictor
from src.model.ranking import rank_position
from src.model.warehouse_graph import WarehouseGraph, WarehouseGraphConfig


st.set_page_config(
    page_title="Warehouse AI Slotting",
    page_icon=":material/inventory_2:",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent


PRIMARY = "#16A34A"        
PRIMARY_HOVER = "#15803D"
PRIMARY_SOFT = "#22C55E"   
PRIMARY_LIGHT = "#F0FDF4"  
PRIMARY_BORDER = "#BBF7D0"
INK = "#111827"
SUBTLE = "#6B7280"
FAINT = "#9CA3AF"
BORDER = "#F1F5F2"
BORDER_STRONG = "#E5E7EB"
SURFACE = "#FFFFFF"
BG = "#FAFBFA"
WARN = "#B45309"
WARN_BG = "#FFFBEB"
DANGER = "#DC2626"

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        .material-symbols-outlined {{
            font-family: 'Material Symbols Outlined';
            font-weight: 400;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            vertical-align: middle;
            -webkit-font-feature-settings: 'liga';
            font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }}
        .msym-sm {{ font-size: 16px; }}
        .msym-lg {{ font-size: 26px; }}

        .stApp {{ background: {BG}; }}

        /* ---------- Ẩn header/footer mặc định ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        /*header {{visibility: hidden;}}*/

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background: {SURFACE};
            border-right: 1px solid {BORDER_STRONG};
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 1.5rem;
        }}

        /* ---------- Top banner ---------- */
        .app-header {{
            background: linear-gradient(120deg, {PRIMARY_SOFT} 0%, {PRIMARY} 55%, {PRIMARY_HOVER} 100%);
            border-radius: 20px;
            padding: 30px 34px;
            margin-bottom: 22px;
            color: white;
            box-shadow: 0 10px 28px rgba(22,163,74,0.20);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .app-header .left {{ max-width: 640px; }}
        .app-header h1 {{
            margin: 0;
            font-size: 25px;
            font-weight: 800;
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .app-header p {{
            margin: 8px 0 0 0;
            opacity: 0.92;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.5;
        }}
        .app-header .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.32);
            padding: 4px 13px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 12px;
        }}
        .app-header .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.30);
            padding: 8px 16px;
            border-radius: 999px;
            font-size: 12.5px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .pulse-dot {{
            width: 8px; height: 8px; border-radius: 50%;
            background: #FFFFFF;
            box-shadow: 0 0 0 rgba(255,255,255,0.6);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255,255,255,0.55); }}
            70% {{ box-shadow: 0 0 0 8px rgba(255,255,255,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255,255,255,0); }}
        }}

        /* ---------- Section title ---------- */
        .section-title {{
            display: flex;
            align-items: center;
            gap: 9px;
            font-size: 15.5px;
            font-weight: 700;
            color: {INK};
            margin: 6px 0 12px 0;
            padding-bottom: 9px;
            border-bottom: 2px solid {BORDER};
        }}
        .section-title .icon-chip {{
            width: 26px; height: 26px;
            border-radius: 8px;
            background: {PRIMARY_LIGHT};
            display: flex; align-items: center; justify-content: center;
            color: {PRIMARY};
        }}
        .section-title .sub {{
            font-size: 12px;
            font-weight: 400;
            color: {FAINT};
            margin-left: 4px;
        }}

        /* ---------- Card container ---------- */
        .card {{
            background: {SURFACE};
            border: 1px solid {BORDER_STRONG};
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 1px 3px rgba(16,24,20,0.04);
        }}
        .card-head {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 16px;
            margin-bottom: 16px;
            border-bottom: 1px solid {BORDER};
        }}
        .card-head .icon-box {{
            width: 34px; height: 34px;
            border-radius: 10px;
            background: {PRIMARY_LIGHT};
            display: flex; align-items: center; justify-content: center;
            color: {PRIMARY};
            flex-shrink: 0;
        }}
        .card-head .title {{
            font-size: 14.5px;
            font-weight: 700;
            color: {INK};
            margin: 0;
        }}
        .card-head .subtitle {{
            font-size: 12px;
            color: {FAINT};
            margin: 1px 0 0 0;
        }}

        .field-label {{
            font-size: 11.5px;
            font-weight: 600;
            color: {SUBTLE};
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        /* ---------- Inputs ---------- */
        div[data-baseweb="select"] > div {{
            border-radius: 12px !important;
            border-color: {BORDER_STRONG} !important;
        }}
        .stTextInput input, .stNumberInput input {{
            border-radius: 12px !important;
            border-color: {BORDER_STRONG} !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus {{
            border-color: {PRIMARY} !important;
            box-shadow: 0 0 0 2px {PRIMARY_LIGHT} !important;
        }}
        .stCheckbox label p {{ font-weight: 500; }}

        /* ---------- Buttons ---------- */
        .stButton button, .stFormSubmitButton button {{
            background: {PRIMARY} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            padding: 10px 22px !important;
            box-shadow: 0 4px 12px rgba(22,163,74,0.22);
            transition: all 0.15s ease-in-out;
        }}
        .stButton button:hover, .stFormSubmitButton button:hover {{
            background: {PRIMARY_HOVER} !important;
            transform: translateY(-1px);
        }}
        .stButton button p, .stFormSubmitButton button p {{ font-weight: 700 !important; }}

        /* ---------- Radio as pill toggle (chế độ xem sơ đồ) ---------- */
        div[role="radiogroup"] {{ gap: 6px; }}
        div[role="radiogroup"] label {{
            background: {BORDER};
            border-radius: 10px;
            padding: 4px 12px !important;
            margin: 0 !important;
        }}

        /* ---------- Metric-style badges ---------- */
        .metric-box {{
            background: {PRIMARY_LIGHT};
            border: 1px solid {BORDER_STRONG};
            border-radius: 16px;
            padding: 14px 16px;
        }}
        .metric-box .label {{
            font-size: 11px;
            font-weight: 600;
            color: {SUBTLE};
            text-transform: uppercase;
            letter-spacing: 0.4px;
            display: flex; align-items: center; gap: 5px;
        }}
        .metric-box .value {{
            font-size: 21px;
            font-weight: 800;
            color: {PRIMARY_HOVER};
            margin-top: 3px;
        }}

        .stat-strip {{
            display: flex;
            gap: 10px;
            margin-bottom: 4px;
            flex-wrap: wrap;
        }}
        .stat-tile {{
            flex: 1;
            min-width: 140px;
            background: {SURFACE};
            border: 1px solid {BORDER_STRONG};
            border-radius: 14px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .stat-tile .icon-box {{
            width: 32px; height: 32px;
            border-radius: 9px;
            background: {PRIMARY_LIGHT};
            color: {PRIMARY};
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
        }}
        .stat-tile .num {{ font-size: 16px; font-weight: 800; color: {INK}; line-height: 1.1; }}
        .stat-tile .lbl {{ font-size: 10.5px; color: {FAINT}; font-weight: 600; text-transform: uppercase; letter-spacing: .3px; }}

        /* ---------- Dataframe polish ---------- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER_STRONG};
            border-radius: 14px;
            overflow: hidden;
        }}

        .helper-text {{
            font-size: 12.5px;
            color: {FAINT};
            margin-top: 10px;
            margin-bottom: 0;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 44px 20px;
            text-align: center;
        }}
        .empty-state .icon-box {{
            width: 56px; height: 56px;
            border-radius: 16px;
            background: {BORDER};
            display: flex; align-items: center; justify-content: center;
            color: {FAINT};
            margin-bottom: 14px;
        }}
        .empty-state .title {{ font-size: 13.5px; font-weight: 600; color: {SUBTLE}; }}
        .empty-state .sub {{ font-size: 12px; color: {FAINT}; margin-top: 4px; line-height: 1.5; }}

        /* ---------- Detail tiles (result card) ---------- */
        .detail-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 18px;
        }}
        .detail-tile {{
            background: #F9FAF9;
            border-radius: 14px;
            padding: 12px 14px;
        }}
        .detail-tile .k {{ font-size: 11.5px; color: {FAINT}; margin-bottom: 2px; }}
        .detail-tile .v {{ font-size: 14px; font-weight: 700; color: {INK}; font-family: 'JetBrains Mono', monospace; }}

        .confidence-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }}
        .confidence-label {{ font-size: 12px; font-weight: 600; color: {SUBTLE}; }}
        .confidence-value {{ font-size: 20px; font-weight: 800; color: {PRIMARY_HOVER}; }}
        .confidence-track {{ height: 8px; background: {BORDER}; border-radius: 999px; overflow: hidden; margin-bottom: 18px; }}
        .confidence-fill {{ height: 100%; background: linear-gradient(90deg, {PRIMARY_SOFT}, {PRIMARY}); border-radius: 999px; }}

        .factor-title {{ font-size: 11.5px; font-weight: 700; color: {SUBTLE}; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 10px; }}
        .factor-row {{
            display: flex; align-items: flex-start; gap: 10px;
            padding: 10px 12px; border-radius: 12px;
            background: {PRIMARY_LIGHT}; color: {PRIMARY_HOVER};
            font-size: 12.5px; margin-bottom: 6px;
        }}
        .factor-row .msym {{ color: {PRIMARY}; flex-shrink: 0; margin-top: 1px; }}

        /* ---------- Top-5 rank cards ---------- */
        .rank-card {{
            position: relative;
            border-radius: 16px;
            padding: 16px;
            border: 1.5px solid {BORDER_STRONG};
            background: {SURFACE};
            height: 100%;
        }}
        .rank-card.best {{
            border-color: {PRIMARY};
            background: {PRIMARY_LIGHT};
            box-shadow: 0 4px 14px rgba(22,163,74,0.14);
        }}
        .rank-card .best-badge {{
            position: absolute; top: -11px; left: 50%; transform: translateX(-50%);
            background: {PRIMARY};
            color: white;
            font-size: 9.5px; font-weight: 800;
            letter-spacing: 0.4px;
            padding: 3px 11px;
            border-radius: 999px;
            box-shadow: 0 2px 6px rgba(22,163,74,0.3);
            white-space: nowrap;
        }}
        .rank-card .top-row {{ display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px; margin-top: 4px; }}
        .rank-card .rank-num {{
            width: 28px; height: 28px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 800;
            background: {BORDER}; color: {SUBTLE};
        }}
        .rank-card.best .rank-num {{ background: {PRIMARY}; color: white; }}
        .rank-card .conf {{ text-align: right; }}
        .rank-card .conf .num {{ font-size: 17px; font-weight: 800; color: {INK}; line-height: 1.1; }}
        .rank-card.best .conf .num {{ color: {PRIMARY_HOVER}; }}
        .rank-card .conf .lbl {{ font-size: 9.5px; color: {FAINT}; }}
        .rank-card .row {{ display: flex; justify-content: space-between; font-size: 11.5px; padding: 3px 0; }}
        .rank-card .row .k {{ color: {FAINT}; display: flex; align-items: center; gap: 4px; }}
        .rank-card .row .v {{ font-weight: 700; color: {INK}; font-family: 'JetBrains Mono', monospace; }}
        .rank-card .div {{ border-top: 1px solid {BORDER_STRONG}; margin: 6px 0 4px 0; }}
        .rank-card .bar-track {{ height: 4px; background: {BORDER}; border-radius: 999px; overflow: hidden; margin-top: 10px; }}
        .rank-card .bar-fill {{ height: 100%; border-radius: 999px; background: {FAINT}; }}
        .rank-card.best .bar-fill {{ background: {PRIMARY}; }}

        /* ---------- Legend (sơ đồ kho) ---------- */
        .legend-strip {{ display: flex; gap: 18px; flex-wrap: wrap; margin-top: 4px; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: {SUBTLE}; }}
        .legend-swatch {{ width: 14px; height: 14px; border-radius: 4px; display: inline-block; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def icon(name: str, size_cls: str = "") -> str:
    """Render a Material Symbols icon span for use inside raw HTML blocks."""
    cls = f"material-symbols-outlined {size_cls}".strip()
    return f'<span class="{cls}">{name}</span>'


def legend_item(color: str, border: str, label: str) -> str:
    return (
        f'<div class="legend-item">'
        f'<span class="legend-swatch" style="background:{color};border:2px solid {border};"></span>{label}'
        f"</div>"
    )

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
    dm_san_pham = pd.read_csv(
        BASE_DIR / "./data/clean/dm_san_pham_clean.csv",
        low_memory=False,
    )
    return feature_table, vitri, tonkho, cham, dm_san_pham


@st.cache_resource
def load_predictor(_feature_table):
    predictor = Predictor(
        feature_table=_feature_table,
        model_root=BASE_DIR / "./models",
    )

    return predictor


@st.cache_resource
def load_warehouse_graph(_vitri, kho_id):

    config = WarehouseGraphConfig(
        inbound_gate_count=7,
        outbound_gate_count=6,
    )
    graph = WarehouseGraph.from_positions(_vitri, kho_id=kho_id, config=config)
    return graph, graph.distance_matrix()


feature_table, vitri, tonkho, cham, dm_san_pham = load_data()
predictor = load_predictor(feature_table)



QTY_COLUMNS = ["so_luong_ton", "ton_kho", "so_luong", "quantity", "sl_ton", "sl_ton_kho"]


@st.cache_data
def get_warehouse_positions(vitri_df: pd.DataFrame, tonkho_df: pd.DataFrame, kho_id) -> pd.DataFrame:

    df = vitri_df.copy()
    if "kho_id" in df.columns:
        df = df[df["kho_id"] == kho_id]

    required = {"ma_so_vi_tri", "day_ke_id", "tang"}
    if not required.issubset(df.columns) or df.empty:
        return pd.DataFrame(columns=list(required) + ["pos", "status"])

    df = df.sort_values(["day_ke_id", "tang", "ma_so_vi_tri"]).reset_index(drop=True)
    df["pos"] = df.groupby(["day_ke_id", "tang"]).cumcount() + 1

    occupied_ids = set()

    if tonkho_df is not None:

        # lấy toàn bộ vị trí xuất hiện trong tồn kho
        occupied_ids = set(
            tonkho_df["vi_tri_id"]
            .dropna()
            .astype(df["auto_id"].dtype)
            .unique()
        )

    # auto_id của dm_vi_tri = vi_tri_id của tồn kho
    df["status"] = df["auto_id"].apply(
        lambda x: "occupied" if x in occupied_ids else "available")
    return df


def build_overview_heatmap(positions_df: pd.DataFrame) -> go.Figure:
    """Bản đồ tổng quan toàn kho: % lấp đầy theo (Dãy x Tầng)."""
    summary = (
        positions_df.groupby(["day_ke_id", "tang"])
        .agg(total=("ma_so_vi_tri", "count"), occupied=("status", lambda s: (s == "occupied").sum()))
        .reset_index()
    )
    summary["occ_pct"] = (summary["occupied"] / summary["total"] * 100).round(1)

    racks = sorted(summary["day_ke_id"].unique().tolist(), key=lambda v: str(v))
    floors = sorted(summary["tang"].unique().tolist(), reverse=True)

    z, text = [], []
    for fl in floors:
        row_z, row_text = [], []
        for rk in racks:
            cell = summary[(summary["day_ke_id"] == rk) & (summary["tang"] == fl)]
            if cell.empty:
                row_z.append(None)
                row_text.append("")
            else:
                r = cell.iloc[0]
                row_z.append(r["occ_pct"])
                row_text.append(
                    f"Dãy {rk} · Tầng {fl}<br>Lấp đầy: {r['occ_pct']}%<br>{int(r['occupied'])}/{int(r['total'])} vị trí"
                )
        z.append(row_z)
        text.append(row_text)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[str(r) for r in racks],
            y=[f"Tầng {f}" for f in floors],
            text=text,
            hoverinfo="text",
            colorscale=[[0, "#FFFFFF"], [0.5, PRIMARY_BORDER], [1, PRIMARY]],
            zmin=0,
            zmax=100,
            xgap=4,
            ygap=4,
            colorbar=dict(title="% lấp đầy", ticksuffix="%", thickness=14),
        )
    )
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color=SUBTLE),
        xaxis=dict(title="Dãy kệ", side="bottom", fixedrange=True),
        yaxis=dict(title="", fixedrange=True),
    )
    return fig


def build_rack_detail_figure(positions_df: pd.DataFrame, rack, ranking: pd.DataFrame | None) -> go.Figure:
    """Bản đồ chi tiết 1 dãy kệ: từng ô vị trí theo (Ô x Tầng), tô màu theo trạng thái & gợi ý AI."""
    sub = positions_df[positions_df["day_ke_id"] == rack].copy()

    rec_map = {}
    if ranking is not None and not ranking.empty:
        for i, row in ranking.reset_index(drop=True).iterrows():
            rec_map[row["ma_so_vi_tri"]] = (i + 1, row["score"])

    floors = sorted(sub["tang"].unique().tolist(), reverse=True)

    xs, ys, colors, borders, texts = [], [], [], [], []
    for _, r in sub.iterrows():
        info = rec_map.get(r["ma_so_vi_tri"])
        if info and info[0] == 1:
            fill, border = PRIMARY_SOFT, PRIMARY_HOVER
        elif info:
            fill, border = PRIMARY_BORDER, "#86EFAC"
        elif r["status"] == "occupied":
            fill, border = "#E5E7EB", "#D1D5DB"
        else:
            fill, border = "#FFFFFF", BORDER_STRONG

        xs.append(r["pos"])
        ys.append(f"Tầng {r['tang']}")
        colors.append(fill)
        borders.append(border)

        rank_txt = f"<br>Hạng gợi ý AI: #{info[0]} (điểm {info[1]:.2f})" if info else ""
        status_txt = "Đã sử dụng" if r["status"] == "occupied" else "Trống"
        texts.append(
            f"<b>{r['ma_so_vi_tri']}</b><br>Dãy {r['day_ke_id']} · Tầng {r['tang']} · Ô {r['pos']}"
            f"<br>Trạng thái: {status_txt}{rank_txt}"
        )

    fig = go.Figure(
        data=go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(symbol="square", size=28, color=colors, line=dict(color=borders, width=2)),
            text=texts,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        height=max(320, 68 * max(len(floors), 1)),
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color=SUBTLE),
        xaxis=dict(title="Ô vị trí", dtick=1, zeroline=False, fixedrange=True),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=[f"Tầng {f}" for f in floors],
            fixedrange=True,
        ),
    )
    return fig



# Sidebar — Kho & thông tin hệ thống


with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:11px;margin-bottom:24px;">
            <div style="width:40px;height:40px;border-radius:12px;background:{PRIMARY};
                        display:flex;align-items:center;justify-content:center;color:white;">
                {icon('inventory_2', 'msym-lg')}
            </div>
            <div>
                <div style="font-weight:800;font-size:15.5px;color:{INK};line-height:1.15;">Warehouse AI</div>
                <div style="font-size:12px;color:{FAINT};">Slotting Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="section-title"><span class="icon-chip">{icon("warehouse", "msym-sm")}</span>Kho vận hành</div>',
        unsafe_allow_html=True,
    )

    available_warehouses = sorted(
        int(path.name)
        for path in (BASE_DIR / "models").iterdir()
        if path.is_dir()
        and (path / "RandomForest" / "day_ke_id.pkl").exists()
        and (path / "RandomForest" / "tang.pkl").exists()
    )
    if not available_warehouses:
        st.error("Không tìm thấy model RandomForest đã huấn luyện cho kho nào.")
        st.stop()

    warehouse = st.selectbox(
        "Chọn kho",
        available_warehouses,
        label_visibility="collapsed",
    )

    if st.session_state.get("_loaded_warehouse") != warehouse:
        with st.spinner(f"Đang tải mô hình cho kho {warehouse}..."):
            predictor.load_model(warehouse)
        st.session_state["_loaded_warehouse"] = warehouse

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-title"><span class="icon-chip">{icon("database", "msym-sm")}</span>Trạng thái dữ liệu</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box" style="margin-bottom:10px;">
            <div class="label">{icon('category', 'msym-sm')} Sản phẩm</div>
            <div class="value">{dm_san_pham['auto_id'].nunique():,}</div>
        </div>
        <div class="metric-box">
            <div class="label">{icon('grid_view', 'msym-sm')} Vị trí trong kho</div>
            <div class="value">{vitri.shape[0]:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.caption("© Warehouse AI · Slotting Engine v1.0")



st.markdown(
    f"""
    <div class="app-header">
        <div class="left">
            <span class="badge">{icon('bolt', 'msym-sm')} AI Slotting Engine</span>
            <h1>{icon('target', 'msym-lg')} Gợi ý vị trí lưu trữ hàng hóa</h1>
            <p>Nhập thông tin sản phẩm và số lượng nhập kho — hệ thống AI sẽ đề xuất vị trí lưu trữ tối ưu theo dãy, tầng và ô kệ.</p>
        </div>
        <div class="status-pill"><span class="pulse-dot"></span>Model sẵn sàng</div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    f'<div class="section-title"><span class="icon-chip">{icon("package_2", "msym-sm")}</span>Thông tin sản phẩm</div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    is_new_product = st.checkbox(":material/add_circle: Đây là sản phẩm mới (chưa có trong hệ thống)")

    products = (
        dm_san_pham[
            [
                "auto_id",
                "ma_san_pham",
                "ten_san_pham",
                "nganh_hang_id",
                "gw_san_pham",
                "cbm_san_pham",
            ]
        ]
        .drop_duplicates()
    )

    nganh_options = (
        dm_san_pham["nganh_hang_id"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if not is_new_product:

        selected = st.selectbox(
            ":material/search: Sản phẩm",
            options=products.to_dict("records"),
            format_func=lambda x: f"{x['ma_san_pham']} - {x['ten_san_pham']}",
        )

        auto_id = selected["auto_id"]
        ten_san_pham = selected["ten_san_pham"]

        nganh_hang_id = selected["nganh_hang_id"]
        gw = float(selected["gw_san_pham"])
        cbm = float(selected["cbm_san_pham"])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input(":material/category: Ngành hàng", value=str(nganh_hang_id), disabled=True)
        with c2:
            st.number_input(":material/scale: GW (kg)", value=gw, disabled=True)
        with c3:
            st.number_input(":material/deployed_code: CBM (cm³)", value=cbm, disabled=True)

    else:

        auto_id = -1

        c1, c2 = st.columns(2)
        with c1:
            st.text_input(":material/tag: Mã sản phẩm")
        with c2:
            st.text_input(":material/label: Tên sản phẩm")

        c3, c4, c5 = st.columns(3)
        with c3:
            nganh_hang_id = st.selectbox(":material/category: Ngành hàng", options=nganh_options)
        with c4:
            gw = st.number_input(":material/scale: GW (kg)", value=0.0)
        with c5:
            cbm = st.number_input(":material/deployed_code: CBM (cm³)", value=0.0)

    st.markdown('</div>', unsafe_allow_html=True)



st.markdown(
    f'<div class="section-title"><span class="icon-chip">{icon("move_to_inbox", "msym-sm")}</span>Thông số nhập kho</div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    with st.form("predict"):

        col1, col2 = st.columns(2)

        with col1:
            shelf = st.number_input(
                ":material/calendar_month: Số ngày sử dụng còn lại",
                value=0,
            )

        with col2:
            quantity = st.number_input(
                ":material/inventory: Số lượng nhập",
                value=0,
            )

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        submit = st.form_submit_button(
            "Gợi ý vị trí lưu trữ",
            icon=":material/bolt:",
            use_container_width=False,
        )

    st.markdown('</div>', unsafe_allow_html=True)


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

    with st.spinner("Đang phân tích dữ liệu kho vận..."):
        warehouse_graph, distance_matrix = load_warehouse_graph(vitri, warehouse)
        result = predictor.predict(product, target_vi_tri_type_id=2)
        ranking = rank_position(
            predictor_result=result,
            product=product,
            vitri=vitri,
            tonkho=tonkho,
            cham=cham,
            top_k=5,
            target_vi_tri_type_id=2,
            distance_matrix=distance_matrix,
            warehouse_graph=warehouse_graph,
        )

    st.session_state["wh_warehouse"] = warehouse
    st.session_state["wh_result"] = result
    st.session_state["wh_ranking"] = ranking

current_result = None
current_ranking = None
if st.session_state.get("wh_warehouse") == warehouse:
    current_result = st.session_state.get("wh_result")
    current_ranking = st.session_state.get("wh_ranking")
    if current_ranking is not None and not {
        "inbound_distance_m", "outbound_distance_m", "same_sku_distance_m"
    }.issubset(current_ranking.columns):
        current_result = None
        current_ranking = None

st.markdown(
    f"""<div class="section-title">
        <span class="icon-chip">{icon("map", "msym-sm")}</span>Sơ đồ kho 2D
        <span class="sub">Trực quan hoá vị trí theo dãy &amp; tầng — Kho {warehouse}</span>
    </div>""",
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    positions_df = get_warehouse_positions(vitri, tonkho, warehouse)

    if positions_df.empty:
        st.markdown(
            f"""<div class="empty-state">
                <div class="icon-box">{icon('map', 'msym-lg')}</div>
                <div class="title">Chưa có dữ liệu vị trí cho kho này</div>
                <div class="sub">Kiểm tra lại cột kho_id / day_ke_id / tang trong bảng dm_vi_tri.</div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        total_pos = len(positions_df)
        available_pos = int((positions_df["status"] == "available").sum())
        occupied_pos = total_pos - available_pos
        fill_pct = round(occupied_pos / total_pos * 100) if total_pos else 0

        st.markdown(
            f"""
            <div class="stat-strip" style="margin-bottom:18px;">
                <div class="stat-tile"><div class="icon-box">{icon('grid_view','msym-sm')}</div>
                    <div><div class="num">{total_pos:,}</div><div class="lbl">Tổng vị trí</div></div></div>
                <div class="stat-tile"><div class="icon-box">{icon('check_circle','msym-sm')}</div>
                    <div><div class="num">{available_pos:,}</div><div class="lbl">Còn trống</div></div></div>
                <div class="stat-tile"><div class="icon-box">{icon('inventory','msym-sm')}</div>
                    <div><div class="num">{occupied_pos:,}</div><div class="lbl">Đã sử dụng</div></div></div>
                <div class="stat-tile"><div class="icon-box">{icon('percent','msym-sm')}</div>
                    <div><div class="num">{fill_pct}%</div><div class="lbl">Tỉ lệ lấp đầy</div></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        map_mode = st.radio(
            "Chế độ xem",
            options=["overview", "rack"],
            format_func=lambda m: "Tổng quan kho" if m == "overview" else "Chi tiết theo dãy",
            horizontal=True,
            label_visibility="collapsed",
            key="map_mode",
        )

        if map_mode == "overview":
            st.plotly_chart(
                build_overview_heatmap(positions_df),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f'<div class="helper-text">{icon("info", "msym-sm")} '
                f'Màu càng đậm, dãy/tầng càng lấp đầy. Chuyển sang "Chi tiết theo dãy" để xem từng ô vị trí '
                f"và các vị trí AI vừa gợi ý.</div>",
                unsafe_allow_html=True,
            )
        else:
            racks = sorted(positions_df["day_ke_id"].unique().tolist(), key=lambda v: str(v))
            default_rack = racks[0]
            if current_ranking is not None and not current_ranking.empty:
                top_rack = current_ranking.iloc[0]["day_ke_id"]
                if top_rack in racks:
                    default_rack = top_rack

            selected_rack = st.selectbox(
                ":material/view_column: Chọn dãy kệ",
                options=racks,
                index=racks.index(default_rack),
            )

            st.plotly_chart(
                build_rack_detail_figure(positions_df, selected_rack, current_ranking),
                use_container_width=True,
                config={"displayModeBar": False},
            )

            st.markdown(
                f"""
                <div class="legend-strip">
                    {legend_item('#FFFFFF', BORDER_STRONG, 'Trống')}
                    {legend_item('#E5E7EB', '#D1D5DB', 'Đã sử dụng')}
                    {legend_item(PRIMARY_BORDER, '#86EFAC', 'Trong top 5 gợi ý AI')}
                    {legend_item(PRIMARY_SOFT, PRIMARY_HOVER, 'Vị trí tốt nhất')}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

# Kết quả gợi ý AI (chỉ hiển thị khi đã có dự đoán cho kho hiện tại)

if current_result is not None and current_ranking is not None:

    result = current_result
    ranking = current_ranking

    st.markdown(
        f'<div class="section-title"><span class="icon-chip">{icon("neurology", "msym-sm")}</span>Kết quả gợi ý AI</div>',
        unsafe_allow_html=True,
    )

    # Day & Tầng — hiển thị song song dạng card

    col_day, col_tang = st.columns(2)

    with col_day:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card-head">
                <div class="icon-box">{icon('view_column', 'msym-sm')}</div>
                <div>
                    <p class="title">Top Dãy đề xuất</p>
                    <p class="subtitle">Xếp hạng theo mức độ phù hợp</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(result["day_prediction"], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_tang:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card-head">
                <div class="icon-box">{icon('layers', 'msym-sm')}</div>
                <div>
                    <p class="title">Top Tầng đề xuất</p>
                    <p class="subtitle">Xếp hạng theo mức độ phù hợp</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(result["tang_prediction"], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Kết quả chính (AI Recommendation) + Diễn giải + Top 5

    if ranking.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="empty-state">
                <div class="icon-box">{icon('search_off', 'msym-lg')}</div>
                <div class="title">Không tìm thấy vị trí phù hợp</div>
                <div class="sub">Vui lòng kiểm tra lại thông số nhập kho và thử lại.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        top1 = ranking.iloc[0]

        if bool(top1["empty"]):
            trang_thai, trang_thai_icon = "Trống", "check_circle"
        elif bool(top1["same_product"]):
            trang_thai, trang_thai_icon = "Cùng sản phẩm", "join_inner"
        else:
            trang_thai, trang_thai_icon = "Đã sử dụng", "inventory"

        col_main, col_side = st.columns([1, 1])

        with col_main:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="card-head">
                    <div class="icon-box">{icon('target', 'msym-sm')}</div>
                    <div>
                        <p class="title">Gợi ý AI — Vị trí tốt nhất</p>
                        <p class="subtitle">Kết quả đầu ra của mô hình xếp hạng</p>
                    </div>
                </div>
                <div class="detail-grid">
                    <div class="detail-tile">
                        <div class="k">Vị trí</div>
                        <div class="v">{top1['ma_so_vi_tri']}</div>
                    </div>
                    <div class="detail-tile">
                        <div class="k">Dãy kệ</div>
                        <div class="v">{top1['day_ke_id']}</div>
                    </div>
                    <div class="detail-tile">
                        <div class="k">Tầng</div>
                        <div class="v">Tầng {top1['tang']}</div>
                    </div>
                    <div class="detail-tile">
                        <div class="k">Trạng thái</div>
                        <div class="v" style="display:flex;align-items:center;gap:5px;font-size:12.5px;">
                            {icon(trang_thai_icon, 'msym-sm')} {trang_thai}
                        </div>
                    </div>
                    <div class="detail-tile">
                        <div class="k">Đường từ cổng nhập</div>
                        <div class="v">{top1['inbound_distance_m']:.1f} m</div>
                    </div>
                    <div class="detail-tile">
                        <div class="k">Đường đến cổng xuất</div>
                        <div class="v">{top1['outbound_distance_m']:.1f} m</div>
                    </div>
                </div>
                <div class="confidence-row">
                    <span class="confidence-label">ĐIỂM PHÙ HỢP</span>
                    <span class="confidence-value">{top1['score']:.2f}</span>
                </div>
                <div class="confidence-track">
                    <div class="confidence-fill" style="width:{min(max(float(top1['score']) * 100, 4), 100)}%;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_side:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="card-head">
                    <div class="icon-box">{icon('psychology', 'msym-sm')}</div>
                    <div>
                        <p class="title">Diễn giải của AI</p>
                        <p class="subtitle">Các yếu tố ảnh hưởng đến điểm số</p>
                    </div>
                </div>
                <div class="factor-row">
                    <span class="msym material-symbols-outlined msym-sm">trending_up</span>
                    <span>Tần suất xuất kho cao được ghi nhận cho sản phẩm này</span>
                </div>
                <div class="factor-row">
                    <span class="msym material-symbols-outlined msym-sm">workspace_premium</span>
                    <span>Vị trí phù hợp với nhóm ngành hàng ưu tiên</span>
                </div>
                <div class="factor-row">
                    <span class="msym material-symbols-outlined msym-sm">crop_free</span>
                    <span>Sức chứa còn trống đủ đáp ứng số lượng nhập kho</span>
                </div>
                <div class="factor-row">
                    <span class="msym material-symbols-outlined msym-sm">hub</span>
                    <span>Có sản phẩm tương đồng gần vị trí này trong cùng dãy kệ</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Top 5 vị trí — dạng thẻ xếp hạng

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card-head">
                <div class="icon-box">{icon('location_on', 'msym-sm')}</div>
                <div>
                    <p class="title">Top 5 vị trí lưu trữ tối ưu</p>
                    <p class="subtitle">Xếp hạng theo điểm phù hợp — ưu tiên vị trí trống hoặc cùng nhóm sản phẩm</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        top5 = ranking.head(5).reset_index(drop=True)
        max_score = float(top5["score"].max()) or 1.0
        cols = st.columns(len(top5))

        for i, (col, (_, row)) in enumerate(zip(cols, top5.iterrows())):
            is_best = i == 0
            trang_thai_row = (
                "Trống" if bool(row["empty"])
                else "Cùng SP" if bool(row["same_product"])
                else "Đã dùng"
            )
            bar_pct = max(min(float(row["score"]) / max_score * 100, 100), 6)

            badge_html = (
                f'<div class="best-badge">{icon("military_tech", "msym-sm")} PHÙ HỢP NHẤT</div>'
                if is_best else ""
            )


            card_html = (
                f'<div class="rank-card {"best" if is_best else ""}">'
                f"{badge_html}"
                f'<div class="top-row">'
                f'<div class="rank-num">#{i + 1}</div>'
                f'<div class="conf"><div class="num">{row["score"]:.2f}</div><div class="lbl">điểm</div></div>'
                f"</div>"
                f'<div class="row"><span class="k">{icon("view_column", "msym-sm")} Dãy</span><span class="v">{row["day_ke_id"]}</span></div>'
                f'<div class="row"><span class="k">{icon("layers", "msym-sm")} Tầng</span><span class="v">{row["tang"]}</span></div>'
                f'<div class="row"><span class="k">{icon("location_on", "msym-sm")} Vị trí</span><span class="v">{row["ma_so_vi_tri"]}</span></div>'
                f'<div class="row"><span class="k">{icon("route", "msym-sm")} Cổng nhập</span><span class="v">{row["inbound_distance_m"]:.1f} m</span></div>'
                f'<div class="div"></div>'
                f'<div class="row"><span class="k">Trạng thái</span><span class="v">{trang_thai_row}</span></div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{bar_pct}%;"></div></div>'
                f"</div>"
            )

            with col:
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


        with st.expander(":material/table_rows: Xem bảng chi tiết đầy đủ"):
            display_df = ranking[
                [
                    "ma_so_vi_tri",
                    "day_ke_id",
                    "tang",
                    "score",
                    "inbound_distance_m",
                    "outbound_distance_m",
                    "same_sku_distance_m",
                    "capacity_fit",
                    "same_product",
                    "empty",
                ]
            ].rename(
                columns={
                    "ma_so_vi_tri": "Vị trí",
                    "day_ke_id": "Dãy kệ",
                    "tang": "Tầng",
                    "score": "Điểm phù hợp",
                    "inbound_distance_m": "Đường từ cổng nhập (m)",
                    "outbound_distance_m": "Đường tới cổng xuất (m)",
                    "same_sku_distance_m": "Khoảng cách tới cùng SKU (m)",
                    "capacity_fit": "Mức đáp ứng sức chứa",
                    "same_product": "Cùng sản phẩm",
                    "empty": "Trống",
                }
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Điểm phù hợp": st.column_config.ProgressColumn(
                        "Điểm phù hợp",
                        format="%.2f",
                        min_value=float(display_df["Điểm phù hợp"].min()),
                        max_value=float(display_df["Điểm phù hợp"].max()) or 1.0,
                    ),
                    "Cùng sản phẩm": st.column_config.CheckboxColumn("Cùng sản phẩm"),
                    "Trống": st.column_config.CheckboxColumn("Trống"),
                },
            )

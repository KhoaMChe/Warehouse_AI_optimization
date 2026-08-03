"""
SLAP DATABASE SETUP
===================
Tạo SQLite database từ dữ liệu thực tế của kho phân phối.

Kiến trúc gồm 3 lớp:
  Layer 1 - Raw tables   : giữ nguyên dữ liệu gốc từ WMS (sanpham, vitri, tonkho...)
  Layer 2 - SLAP tables  : dữ liệu đã xử lý sẵn cho thuật toán (slap_skus, slap_locations...)
  Layer 3 - Result tables: kết quả mỗi lần chạy thuật toán (slap_runs, slap_assignments)

Cách dùng:
    python setup_database.py                      # tạo DB mới
    python setup_database.py --migrate path/csv   # migrate từ thư mục chứa các file CSV
"""

import sqlite3
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slap_warehouse.db")

DDL = """
-- ================================================================
-- LAYER 1: RAW TABLES (giữ nguyên cấu trúc từ WMS)
-- ================================================================

CREATE TABLE IF NOT EXISTS raw_sanpham (
    auto_id                     INTEGER PRIMARY KEY,
    chu_hang_id                 INTEGER,
    nhom_nganh_hang_id          INTEGER,
    nganh_hang_id               INTEGER,
    loai_san_pham_id            INTEGER,
    don_vi_tinh_id              INTEGER,
    don_vi_tinh_thung_id        INTEGER,
    ma_san_pham                 TEXT,
    ten_san_pham                TEXT,
    sl_cai_1_thung              REAL,
    sl_thung_1_pallet           REAL,
    qui_cach_thung_type_id      INTEGER,
    gw_san_pham                 REAL,       -- gross weight (kg) đơn vị SP
    nw_san_pham                 REAL,       -- net weight (kg)
    cbm_san_pham                REAL,       -- thể tích (m3) đơn vị SP
    gw_thung_empty              REAL,
    cbm_item                    REAL,
    sqft                        REAL,
    chien_luoc_put_id           INTEGER,    -- chiến lược putaway
    chien_luoc_pick_id          INTEGER,    -- chiến lược picking
    co_che_fifo_id              INTEGER,
    so_ngay_su_dung             INTEGER,
    don_gia                     REAL,
    gia_mua                     REAL,
    gia_ban                     REAL,
    carton_dai                  REAL,
    carton_rong                 REAL,
    carton_cao                  REAL,
    pcs_dai                     REAL,
    pcs_rong                    REAL,
    pcs_cao                     REAL,
    trang_thai_id               INTEGER,
    san_pham_type_id            INTEGER,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,
    created_by                  TEXT,
    last_updated                TEXT,
    last_updated_by             TEXT
);

CREATE TABLE IF NOT EXISTS raw_vitri (
    auto_id                     INTEGER PRIMARY KEY,
    kho_id                      INTEGER NOT NULL,
    day_ke_id                   INTEGER,
    ma_so_vi_tri                TEXT,
    tang                        TEXT,           -- tầng kệ (A/B/C hoặc 1/2/3...)
    dai                         REAL,           -- chiều dài vị trí (m)
    rong                        REAL,
    cao                         REAL,
    vi_tri_type_id              INTEGER,        -- loại vị trí (pallet/shelf/floor...)
    vi_tri_seq_id               INTEGER,        -- số thứ tự -> dùng tính khoảng cách
    sl_pallet                   INTEGER,
    sl_sku                      INTEGER,
    gw_max                      REAL,           -- tải trọng tối đa (kg)
    cbm_max                     REAL,           -- thể tích tối đa (m3)
    trang_thai_id               INTEGER,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,
    last_updated                TEXT
);

CREATE TABLE IF NOT EXISTS raw_tonkho (
    auto_id                     INTEGER PRIMARY KEY,
    chu_hang_id                 INTEGER,
    kho_id                      INTEGER,
    vi_tri_id                   INTEGER REFERENCES raw_vitri(auto_id),
    so_lpn                      TEXT,
    nhap_kho_id                 INTEGER,
    san_pham_id                 INTEGER REFERENCES raw_sanpham(auto_id),
    so_po                       TEXT,
    ngay_san_xuat               TEXT,
    ngay_het_han                TEXT,
    line_item                   TEXT,
    ma_key_lo_hang              TEXT,
    ngay_nhap_kho_root          TEXT,
    so_kien_nhap                REAL,
    sl_nhap_chan                 REAL,
    sl_nhap_le                  REAL,
    sl_nhap_all_special         REAL,
    so_kien_xuat                REAL,
    sl_xuat_chan                 REAL,
    sl_xuat_le                  REAL,
    sl_xuat_all_special         REAL,
    so_kien_dc                  REAL,
    sl_dc_chan                   REAL,
    sl_dc_le                     REAL,
    sl_dc_all_special            REAL,
    so_kien_tach                REAL,
    don_gia                     REAL,
    nw                          REAL,
    gw                          REAL,
    cbm                         REAL,
    trang_thai_lo_hang_id       INTEGER,
    nv_putaway                  TEXT,
    ngay_gio_putaway            TEXT,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,
    last_updated                TEXT
);

CREATE TABLE IF NOT EXISTS raw_xuatkho (
    auto_id                     INTEGER PRIMARY KEY,
    chu_hang_id                 INTEGER,
    kho_id                      INTEGER,
    xuat_kho_id                 INTEGER,
    xuat_kho_raw_data_id        INTEGER,
    vi_tri_id                   INTEGER REFERENCES raw_vitri(auto_id),
    ton_kho_id                  INTEGER REFERENCES raw_tonkho(auto_id),
    nhap_kho_id                 INTEGER,
    san_pham_id                 INTEGER REFERENCES raw_sanpham(auto_id),
    so_po                       TEXT,
    ngay_san_xuat               TEXT,
    ngay_het_han                TEXT,
    line_item                   TEXT,
    ngay_nhap_kho_root          TEXT,
    so_lpn                      TEXT,
    so_kien_allocated           REAL,
    sl_allocated_chan            REAL,   -- <-- FREQUENCY chính: số kiện nguyên xuất
    sl_allocated_le              REAL,
    sl_allocated_all_special     REAL,
    so_kien_ton_on_allocated    REAL,
    sl_ton_chan_on_allocated     REAL,
    sl_ton_le_on_allocated       REAL,
    sl_ton_all_special_on_allocated REAL,
    don_gia_nhap                REAL,
    don_gia_xuat                REAL,
    gw                          REAL,
    nw                          REAL,
    cbm                         REAL,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,   -- <-- TIMESTAMP để tính frequency theo kỳ
    last_updated                TEXT
);

CREATE TABLE IF NOT EXISTS raw_nhapkho (
    auto_id                     INTEGER PRIMARY KEY,
    nhap_kho_id                 INTEGER,
    san_pham_id                 INTEGER REFERENCES raw_sanpham(auto_id),
    nhap_kho_raw_ref_id         INTEGER,
    so_lpn                      TEXT,
    so_po                       TEXT,
    ngay_san_xuat               TEXT,
    ngay_het_han                TEXT,
    line_item                   TEXT,
    ngay_nhap_kho_root          TEXT,
    ma_key_lo_hang              TEXT,
    so_kien_nhap                REAL,
    sl_nhap_chan                 REAL,
    sl_nhap_le                  REAL,
    sl_nhap_all_special         REAL,
    don_gia                     REAL,
    gw                          REAL,
    nw                          REAL,
    cbm                         REAL,
    trang_thai_lo_hang_rc_id    INTEGER,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,
    last_updated                TEXT
);

CREATE TABLE IF NOT EXISTS raw_cham (
    auto_id                     INTEGER PRIMARY KEY,
    chu_hang_id                 INTEGER,
    kho_id                      INTEGER,
    san_pham_id                 INTEGER REFERENCES raw_sanpham(auto_id),
    xuat_kho_id                 INTEGER,
    ton_kho_id                  INTEGER,
    so_lpn                      TEXT,
    ma_so_vi_tri_cu             TEXT,
    ma_so_vi_tri_moi            TEXT,
    vi_tri_cu_id                INTEGER REFERENCES raw_vitri(auto_id),
    vi_tri_moi_id               INTEGER REFERENCES raw_vitri(auto_id),
    ma_so_vi_tri_actual         TEXT,
    so_kien_repleshniment       REAL,
    sl_repleshniment_chan        REAL,
    sl_repleshniment_le          REAL,
    sl_repleshniment_all_special REAL,
    trang_thai_id               INTEGER,
    is_repleshniment_sau        INTEGER,
    nv_cham_hang                TEXT,
    ngay_gio_bd_cham            TEXT,
    ngay_gio_kt_cham            TEXT,
    deleted                     INTEGER DEFAULT 0,
    created                     TEXT,
    last_updated                TEXT
);

-- ================================================================
-- LAYER 2: SLAP TABLES (đã xử lý, sẵn dùng cho thuật toán)
-- ================================================================

-- Khoảng cách từ mỗi vị trí tới điểm xuất hàng (I/O point)
-- Cần bổ sung thủ công hoặc tính từ vi_tri_seq_id
CREATE TABLE IF NOT EXISTS slap_location_distance (
    vitri_id        INTEGER PRIMARY KEY REFERENCES raw_vitri(auto_id),
    kho_id          INTEGER NOT NULL,
    ma_so_vi_tri    TEXT,
    distance_m      REAL,           -- khoảng cách thực đo hoặc ước tính
    distance_method TEXT DEFAULT 'manual',  -- 'manual' | 'seq_based' | 'coord_based'
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- Thống kê SKU theo kỳ (dùng làm input cho SLAP)
-- Refresh định kỳ bằng slap_refresh_sku_stats()
CREATE TABLE IF NOT EXISTS slap_sku_stats (
    stats_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    san_pham_id     INTEGER REFERENCES raw_sanpham(auto_id),
    kho_id          INTEGER,
    period_start    TEXT NOT NULL,  -- '2024-01-01'
    period_end      TEXT NOT NULL,  -- '2024-03-31'
    freq_orders     INTEGER,        -- số lần xuất (đơn hàng)
    freq_kien_chan   REAL,           -- tổng kiện nguyên xuất -> frequency chính
    freq_kien_le     REAL,
    abc_class       TEXT,           -- 'A' | 'B' | 'C' (tính tự động)
    gw_per_unit     REAL,           -- từ sanpham.gw_san_pham
    cbm_per_unit    REAL,           -- từ sanpham.cbm_san_pham
    calculated_at   TEXT DEFAULT (datetime('now')),
    UNIQUE(san_pham_id, kho_id, period_start, period_end)
);

-- ================================================================
-- LAYER 3: RESULT TABLES (mỗi lần chạy thuật toán)
-- ================================================================

-- Mỗi lần chạy Greedy/GRASP/NSGA-II = 1 bản ghi
CREATE TABLE IF NOT EXISTS slap_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kho_id          INTEGER,
    algorithm       TEXT NOT NULL,          -- 'greedy' | 'grasp' | 'nsga2'
    stats_period    TEXT,                   -- period_start dùng làm input
    params          TEXT,                   -- JSON: {"alpha": 3, "iterations": 30}
    n_skus          INTEGER,
    n_locations     INTEGER,
    total_weighted_dist REAL,               -- hàm mục tiêu 1 (minimize)
    avg_utilization REAL,                   -- hàm mục tiêu 2 (maximize)
    n_violations    INTEGER,                -- số vi phạm ràng buộc
    runtime_ms      REAL,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Chi tiết gán từng SKU vào vị trí
CREATE TABLE IF NOT EXISTS slap_assignments (
    assignment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES slap_runs(run_id),
    san_pham_id     INTEGER REFERENCES raw_sanpham(auto_id),
    vitri_id        INTEGER REFERENCES raw_vitri(auto_id),
    kho_id          INTEGER,
    freq_used       REAL,       -- frequency tại thời điểm chạy
    distance_m      REAL,       -- khoảng cách vị trí được gán
    weighted_dist   REAL,       -- freq * distance
    is_feasible     INTEGER,    -- 1 nếu thỏa ràng buộc, 0 nếu vi phạm
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ================================================================
-- INDEXES
-- ================================================================
CREATE INDEX IF NOT EXISTS idx_tonkho_sanpham  ON raw_tonkho(san_pham_id);
CREATE INDEX IF NOT EXISTS idx_tonkho_vitri    ON raw_tonkho(vi_tri_id);
CREATE INDEX IF NOT EXISTS idx_tonkho_kho      ON raw_tonkho(kho_id);
CREATE INDEX IF NOT EXISTS idx_xuatkho_sp      ON raw_xuatkho(san_pham_id, kho_id);
CREATE INDEX IF NOT EXISTS idx_xuatkho_created ON raw_xuatkho(created);
CREATE INDEX IF NOT EXISTS idx_vitri_kho       ON raw_vitri(kho_id, vi_tri_type_id);
CREATE INDEX IF NOT EXISTS idx_assign_run      ON slap_assignments(run_id);
CREATE INDEX IF NOT EXISTS idx_stats_sp        ON slap_sku_stats(san_pham_id, kho_id);

-- ================================================================
-- VIEWS (truy vấn nhanh không cần viết JOIN lại)
-- ================================================================

-- View: input SLAP đầy đủ cho 1 kho (join stats + sanpham + vitri + distance)
CREATE VIEW IF NOT EXISTS v_slap_input AS
SELECT
    ss.san_pham_id,
    sp.ma_san_pham,
    sp.ten_san_pham,
    ss.kho_id,
    ss.period_start,
    ss.period_end,
    ss.freq_kien_chan          AS frequency,
    ss.abc_class,
    sp.gw_san_pham             AS weight_kg,
    sp.cbm_san_pham            AS volume_m3,
    sp.chien_luoc_put_id,
    sp.chien_luoc_pick_id,
    v.auto_id                  AS vitri_id,
    v.ma_so_vi_tri,
    v.tang,
    v.vi_tri_type_id,
    v.gw_max                   AS max_weight_kg,
    v.cbm_max                  AS max_volume_m3,
    ld.distance_m
FROM slap_sku_stats ss
JOIN raw_sanpham sp ON sp.auto_id = ss.san_pham_id
JOIN raw_vitri v    ON v.kho_id   = ss.kho_id AND v.deleted = 0
LEFT JOIN slap_location_distance ld ON ld.vitri_id = v.auto_id
WHERE ss.kho_id = v.kho_id;

-- View: so sánh kết quả các lần chạy
CREATE VIEW IF NOT EXISTS v_run_comparison AS
SELECT
    r.run_id,
    r.algorithm,
    r.kho_id,
    r.n_skus,
    r.n_locations,
    ROUND(r.total_weighted_dist, 0)   AS total_dist,
    ROUND(r.avg_utilization * 100, 1) AS utilization_pct,
    r.n_violations,
    ROUND(r.runtime_ms, 1)            AS ms,
    r.created_at,
    r.notes
FROM slap_runs r
ORDER BY r.created_at DESC;

-- View: assignment hiện tại của kho (từ tonkho - trạng thái thực tế)
CREATE VIEW IF NOT EXISTS v_current_assignment AS
SELECT
    tk.kho_id,
    tk.vi_tri_id,
    vt.ma_so_vi_tri,
    vt.tang,
    vt.vi_tri_type_id,
    tk.san_pham_id,
    sp.ma_san_pham,
    sp.ten_san_pham,
    SUM(tk.sl_nhap_chan - tk.sl_xuat_chan) AS ton_kho_chan,
    vt.gw_max,
    vt.cbm_max
FROM raw_tonkho tk
JOIN raw_sanpham sp ON sp.auto_id = tk.san_pham_id
JOIN raw_vitri   vt ON vt.auto_id = tk.vi_tri_id
WHERE tk.deleted = 0
GROUP BY tk.vi_tri_id, tk.san_pham_id;
"""

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def create_database(db_path=DB_PATH):
    """Tạo database và toàn bộ schema."""
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.commit()
    print(f"Database đã tạo: {db_path}")
    _print_summary(conn)
    conn.close()


def migrate_from_dataframes(dfs: dict, db_path=DB_PATH):
    """
    Migrate pandas DataFrames vào raw tables.

    dfs = {
        'sanpham': df_sanpham,
        'vitri'  : df_vitri,
        'tonkho' : df_tonkho,
        'xuatkho': df_xuatkho,
        'nhapkho': df_nhapkho,
        'cham'   : df_cham,
    }
    """
    import pandas as pd
    conn = sqlite3.connect(db_path)
    table_map = {
        'sanpham': 'raw_sanpham',
        'vitri'  : 'raw_vitri',
        'tonkho' : 'raw_tonkho',
        'xuatkho': 'raw_xuatkho',
        'nhapkho': 'raw_nhapkho',
        'cham'   : 'raw_cham',
    }
    for key, df in dfs.items():
        target = table_map.get(key)
        if target is None:
            print(f"  [!] Bỏ qua: '{key}' không có trong table_map")
            continue
        # Chỉ giữ các cột tồn tại trong schema
        cur = conn.execute(f"PRAGMA table_info({target})")
        db_cols = {row[1] for row in cur.fetchall()}
        df_filtered = df[[c for c in df.columns if c in db_cols]]
        df_filtered.to_sql(target, conn, if_exists='append', index=False)
        print(f"  [OK] {key} -> {target}: {len(df_filtered):,} dòng")
    conn.commit()
    conn.close()


def refresh_sku_stats(kho_id: int, period_start: str, period_end: str,
                      db_path=DB_PATH):
    """
    Tính lại slap_sku_stats từ raw_xuatkho cho 1 kho và 1 kỳ thời gian.

    Ví dụ: refresh_sku_stats(1, '2024-01-01', '2024-03-31')
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(f"""
        DELETE FROM slap_sku_stats
        WHERE kho_id = {kho_id}
          AND period_start = '{period_start}'
          AND period_end   = '{period_end}';

        INSERT INTO slap_sku_stats
            (san_pham_id, kho_id, period_start, period_end,
             freq_orders, freq_kien_chan, freq_kien_le,
             abc_class, gw_per_unit, cbm_per_unit)
        SELECT
            x.san_pham_id,
            x.kho_id,
            '{period_start}'         AS period_start,
            '{period_end}'           AS period_end,
            COUNT(DISTINCT x.xuat_kho_id)       AS freq_orders,
            COALESCE(SUM(x.sl_allocated_chan),0) AS freq_kien_chan,
            COALESCE(SUM(x.sl_allocated_le),0)  AS freq_kien_le,
            CASE
                WHEN COALESCE(SUM(x.sl_allocated_chan),0) >=
                     (SELECT PERCENTILE_DISC(0.8) WITHIN GROUP (ORDER BY total)
                      FROM (
                        SELECT SUM(sl_allocated_chan) AS total
                        FROM raw_xuatkho
                        WHERE kho_id = {kho_id}
                          AND deleted = 0
                          AND created BETWEEN '{period_start}' AND '{period_end}'
                        GROUP BY san_pham_id
                      )) THEN 'A'
                WHEN COALESCE(SUM(x.sl_allocated_chan),0) >= 1 THEN 'B'
                ELSE 'C'
            END                                  AS abc_class,
            sp.gw_san_pham                       AS gw_per_unit,
            sp.cbm_san_pham                      AS cbm_per_unit
        FROM raw_xuatkho x
        JOIN raw_sanpham sp ON sp.auto_id = x.san_pham_id
        WHERE x.kho_id  = {kho_id}
          AND x.deleted = 0
          AND x.created BETWEEN '{period_start}' AND '{period_end}'
        GROUP BY x.san_pham_id, x.kho_id;
    """)
    # Fallback ABC đơn giản nếu DB không hỗ trợ PERCENTILE_DISC
    conn.execute("""
        UPDATE slap_sku_stats
        SET abc_class = CASE
            WHEN freq_kien_chan >= (
                SELECT AVG(freq_kien_chan)*2
                FROM slap_sku_stats s2
                WHERE s2.kho_id = slap_sku_stats.kho_id
                  AND s2.period_start = slap_sku_stats.period_start
            ) THEN 'A'
            WHEN freq_kien_chan > 0 THEN 'B'
            ELSE 'C'
        END
        WHERE kho_id = ? AND period_start = ?
    """, (kho_id, period_start))
    conn.commit()
    rows = conn.execute(
        "SELECT abc_class, COUNT(*), SUM(freq_kien_chan) "
        "FROM slap_sku_stats WHERE kho_id=? AND period_start=? "
        "GROUP BY abc_class ORDER BY abc_class",
        (kho_id, period_start)
    ).fetchall()
    print(f"\nThống kê SKU kho {kho_id} kỳ {period_start} -> {period_end}:")
    for cls, cnt, total in rows:
        print(f"  Nhóm {cls}: {cnt} SKU, tổng {int(total or 0):,} kiện")
    conn.close()


def save_run_result(result: dict, db_path=DB_PATH) -> int:
    """
    Lưu kết quả 1 lần chạy thuật toán vào DB.

    result = {
        'kho_id': 1,
        'algorithm': 'grasp',
        'params': {'alpha': 3, 'iterations': 30},
        'stats_period': '2024-01-01',
        'n_skus': 120,
        'n_locations': 200,
        'total_weighted_dist': 58432.5,
        'avg_utilization': 0.72,
        'n_violations': 0,
        'runtime_ms': 143.2,
        'notes': 'kho_id=1, vi_tri_type_id=2',
        'assignments': [
            {'san_pham_id': 10, 'vitri_id': 55, 'freq_used': 340,
             'distance_m': 12.5, 'weighted_dist': 4250, 'is_feasible': 1},
            ...
        ]
    }
    Trả về run_id.
    """
    import json
    conn = sqlite3.connect(db_path)
    cur = conn.execute("""
        INSERT INTO slap_runs
            (kho_id, algorithm, stats_period, params, n_skus, n_locations,
             total_weighted_dist, avg_utilization, n_violations, runtime_ms, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        result['kho_id'], result['algorithm'],
        result.get('stats_period'),
        json.dumps(result.get('params', {})),
        result['n_skus'], result['n_locations'],
        result['total_weighted_dist'], result['avg_utilization'],
        result['n_violations'], result['runtime_ms'],
        result.get('notes')
    ))
    run_id = cur.lastrowid
    for a in result.get('assignments', []):
        conn.execute("""
            INSERT INTO slap_assignments
                (run_id, san_pham_id, vitri_id, kho_id,
                 freq_used, distance_m, weighted_dist, is_feasible)
            VALUES (?,?,?,?,?,?,?,?)
        """, (run_id, a['san_pham_id'], a['vitri_id'],
              result['kho_id'], a['freq_used'],
              a['distance_m'], a['weighted_dist'], a['is_feasible']))
    conn.commit()
    conn.close()
    print(f"Đã lưu run #{run_id}: {result['algorithm'].upper()} "
          f"| dist={result['total_weighted_dist']:,.0f} "
          f"| util={result['avg_utilization']*100:.1f}% "
          f"| viol={result['n_violations']}")
    return run_id


def _print_summary(conn):
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    views = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
    ).fetchall()
    print(f"  Tables : {[t[0] for t in tables]}")
    print(f"  Views  : {[v[0] for v in views]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args()
    create_database(args.db)

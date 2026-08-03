"""
SLAP DATABASE SETUP - SQL SERVER (SSMS) VERSION
================================================
Bản chuyển đổi từ setup_database.py (SQLite) sang SQL Server.

Yêu cầu cài đặt:
    pip install pyodbc sqlalchemy pandas

Cần có ODBC Driver 17/18 for SQL Server cài trên máy
(tải tại: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server).

Cách dùng:
    python setup_database_mssql.py --create
    python setup_database_mssql.py --migrate path/to/csv_folder

Chuỗi kết nối lấy từ biến môi trường MSSQL_CONN, hoặc sửa DEFAULT_CONN bên dưới.
Ví dụ (Windows Authentication):
    Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=SLAP_DB;Trusted_Connection=yes;
Ví dụ (SQL Login):
    Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=SLAP_DB;UID=sa;PWD=your_password;
"""

import os
import re
import json
import argparse

import pyodbc
from sqlalchemy import create_engine, text

SCHEMA_SQL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slap_schema_mssql.sql")

DEFAULT_CONN = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=SLAP_DB;"
    "Trusted_Connection=yes;"
)

CONN_STR = os.environ.get("MSSQL_CONN", DEFAULT_CONN)


def get_engine():
    """Trả về SQLAlchemy engine để dùng cho pandas.to_sql, v.v."""
    odbc_connect = pyodbc.connect(CONN_STR).getinfo  # sanity check driver loads
    quoted = CONN_STR.replace(" ", "%20")
    return create_engine(f"mssql+pyodbc:///?odbc_connect={quoted}")


def get_pyodbc_conn():
    """Kết nối pyodbc thô, dùng cho các câu lệnh/stored procedure."""
    return pyodbc.connect(CONN_STR)


def create_database():
    """
    Chạy toàn bộ script slap_schema_mssql.sql trên database đã cấu hình.
    Lưu ý: database (ví dụ SLAP_DB) phải được tạo sẵn trong SSMS trước
    (SQL Server không cho CREATE DATABASE dễ dàng từ script chạy nhiều batch
    kèm theo bước kết nối tới chính DB đó).
    """
    script = None
    for enc in ("utf-8-sig", "utf-8", "cp1258", "cp1252"):
        try:
            with open(SCHEMA_SQL_PATH, "r", encoding=enc) as f:
                script = f.read()
            break
        except UnicodeDecodeError:
            continue
    if script is None:
        raise RuntimeError(
            f"Không đọc được {SCHEMA_SQL_PATH} với các encoding utf-8-sig/utf-8/cp1258/cp1252. "
            "Hãy mở file trong VS Code/Notepad++ và Save with Encoding -> UTF-8."
        )

    # Tách theo GO giống cách SSMS xử lý batch
    batches = re.split(r"^\s*GO\s*$", script, flags=re.IGNORECASE | re.MULTILINE)

    conn = get_pyodbc_conn()
    conn.autocommit = True
    cur = conn.cursor()
    for batch in batches:
        batch = batch.strip()
        if not batch:
            continue
        cur.execute(batch)
    conn.close()
    print("Schema đã được tạo/cập nhật trên SQL Server.")


def migrate_from_dataframes(dfs: dict):
    """
    Migrate pandas DataFrames vào raw tables trên SQL Server.

    dfs = {
        'sanpham': df_sanpham,
        'vitri'  : df_vitri,
        'tonkho' : df_tonkho,
        'xuatkho': df_xuatkho,
        'nhapkho': df_nhapkho,
        'cham'   : df_cham,
    }
    """
    engine = get_engine()
    table_map = {
        'sanpham': 'raw_sanpham',
        'vitri':   'raw_vitri',
        'tonkho':  'raw_tonkho',
        'xuatkho': 'raw_xuatkho',
        'nhapkho': 'raw_nhapkho',
        'cham':    'raw_cham',
    }
    with engine.begin() as conn:
        for key, df in dfs.items():
            target = table_map.get(key)
            if target is None:
                print(f"  [!] Bỏ qua: '{key}' không có trong table_map")
                continue
            cols = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=:t"
            ), {"t": target}).fetchall()
            db_cols = {c[0] for c in cols}
            df_filtered = df[[c for c in df.columns if c in db_cols]]
            df_filtered.to_sql(target, conn, schema="dbo", if_exists="append", index=False)
            print(f"  [OK] {key} -> {target}: {len(df_filtered):,} dòng")


def refresh_sku_stats(kho_id: int, period_start: str, period_end: str):
    """
    Gọi stored procedure dbo.usp_refresh_sku_stats để tính lại slap_sku_stats
    cho 1 kho và 1 kỳ thời gian. In ra thống kê theo nhóm A/B/C.
    """
    conn = get_pyodbc_conn()
    cur = conn.cursor()
    cur.execute(
        "EXEC dbo.usp_refresh_sku_stats @kho_id=?, @period_start=?, @period_end=?",
        kho_id, period_start, period_end
    )
    rows = cur.fetchall()
    conn.commit()
    print(f"\nThống kê SKU kho {kho_id} kỳ {period_start} -> {period_end}:")
    for cls, cnt, total in rows:
        print(f"  Nhóm {cls}: {cnt} SKU, tổng {int(total or 0):,} kiện")
    conn.close()


def save_run_result(result: dict) -> int:
    """
    Lưu kết quả 1 lần chạy thuật toán vào DB (header qua stored procedure,
    chi tiết assignments qua insert hàng loạt bằng executemany).

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
    conn = get_pyodbc_conn()
    cur = conn.cursor()

    cur.execute("""
        DECLARE @run_id INT;
        EXEC dbo.usp_save_run_header
            @kho_id=?, @algorithm=?, @stats_period=?, @params=?,
            @n_skus=?, @n_locations=?, @total_weighted_dist=?,
            @avg_utilization=?, @n_violations=?, @runtime_ms=?, @notes=?,
            @run_id=@run_id OUTPUT;
        SELECT @run_id;
    """,
        result['kho_id'], result['algorithm'],
        result.get('stats_period'),
        json.dumps(result.get('params', {})),
        result['n_skus'], result['n_locations'],
        result['total_weighted_dist'], result['avg_utilization'],
        result['n_violations'], result['runtime_ms'],
        result.get('notes')
    )
    run_id = cur.fetchone()[0]

    assignments = result.get('assignments', [])
    if assignments:
        cur.fast_executemany = True
        cur.executemany("""
            INSERT INTO dbo.slap_assignments
                (run_id, san_pham_id, vitri_id, kho_id,
                 freq_used, distance_m, weighted_dist, is_feasible)
            VALUES (?,?,?,?,?,?,?,?)
        """, [
            (run_id, a['san_pham_id'], a['vitri_id'], result['kho_id'],
             a['freq_used'], a['distance_m'], a['weighted_dist'], a['is_feasible'])
            for a in assignments
        ])

    conn.commit()
    conn.close()
    print(f"Đã lưu run #{run_id}: {result['algorithm'].upper()} "
          f"| dist={result['total_weighted_dist']:,.0f} "
          f"| util={result['avg_utilization']*100:.1f}% "
          f"| viol={result['n_violations']}")
    return run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true", help="Tạo/cập nhật schema trên SQL Server")
    parser.add_argument("--migrate", help="Thư mục chứa CSV để migrate (sanpham.csv, vitri.csv, ...)")
    args = parser.parse_args()

    if args.create:
        create_database()
    elif args.migrate:
        import pandas as pd
        folder = args.migrate
        dfs = {}
        for key in ['sanpham', 'vitri', 'tonkho', 'xuatkho', 'nhapkho', 'cham']:
            path = os.path.join(folder, f"{key}.csv")
            if os.path.exists(path):
                dfs[key] = pd.read_csv(path)
        migrate_from_dataframes(dfs)
    else:
        parser.print_help()
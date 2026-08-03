import sqlite3

conn = sqlite3.connect("slap_warehouse.db")

cursor = conn.cursor()

tables = [
    "raw_sanpham",
    "raw_vitri",
    "raw_tonkho",
    "raw_xuatkho",
    "raw_nhapkho",
    "raw_cham",
]

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:15}: {count:,}")

conn.close()
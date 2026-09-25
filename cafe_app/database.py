import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cafe.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db(force=False):
    """Khởi tạo cơ sở dữ liệu. force=True sẽ xóa dữ liệu cũ và tạo lại từ đầu."""
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    is_new = not os.path.exists(DB_PATH)
    conn = get_connection()
    if is_new:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    else:
        _migrate(conn)
    conn.close()


def _migrate(conn):
    """Thêm cột mới vào cơ sở dữ liệu cũ nếu chưa có (tránh phải xóa dữ liệu khi cập nhật app)."""
    cols = [row['name'] for row in conn.execute('PRAGMA table_info(don_hang)').fetchall()]
    if 'phuong_thuc_tt' not in cols:
        conn.execute('ALTER TABLE don_hang ADD COLUMN phuong_thuc_tt TEXT DEFAULT NULL')
        conn.commit()


def query(sql, args=(), one=False):
    conn = get_connection()
    cur = conn.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, args=()):
    conn = get_connection()
    cur = conn.execute(sql, args)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

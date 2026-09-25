-- Schema quản lý quán cà phê
DROP TABLE IF EXISTS chi_tiet_don;
DROP TABLE IF EXISTS don_hang;
DROP TABLE IF EXISTS ban;
DROP TABLE IF EXISTS mon_an;

CREATE TABLE mon_an (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    loai TEXT NOT NULL DEFAULT 'Đồ uống',   -- 'Đồ uống' hoặc 'Đồ ăn'
    gia INTEGER NOT NULL,
    mo_ta TEXT DEFAULT '',
    con_ban INTEGER NOT NULL DEFAULT 1      -- 1 = còn bán, 0 = ngừng bán
);

CREATE TABLE ban (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    so_ban TEXT NOT NULL,
    trang_thai TEXT NOT NULL DEFAULT 'Trống'  -- 'Trống' hoặc 'Có khách'
);

CREATE TABLE don_hang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ban_id INTEGER,
    ten_khach TEXT DEFAULT '',
    thoi_gian TEXT NOT NULL,
    trang_thai TEXT NOT NULL DEFAULT 'Chờ xác nhận', -- Chờ xác nhận/Đang chuẩn bị/Đã hoàn thành/Đã hủy
    da_thanh_toan INTEGER NOT NULL DEFAULT 0,
    phuong_thuc_tt TEXT DEFAULT NULL,   -- 'Tiền mặt' hoặc 'Chuyển khoản'
    tong_tien INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (ban_id) REFERENCES ban(id)
);

CREATE TABLE chi_tiet_don (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    don_hang_id INTEGER NOT NULL,
    mon_an_id INTEGER,
    ten_mon TEXT NOT NULL,
    gia INTEGER NOT NULL,
    so_luong INTEGER NOT NULL,
    FOREIGN KEY (don_hang_id) REFERENCES don_hang(id),
    FOREIGN KEY (mon_an_id) REFERENCES mon_an(id)
);

-- Dữ liệu mẫu
INSERT INTO mon_an (ten, loai, gia, mo_ta, con_ban) VALUES
('Cà phê đen', 'Đồ uống', 20000, 'Cà phê phin truyền thống', 1),
('Cà phê sữa', 'Đồ uống', 25000, 'Cà phê phin kèm sữa đặc', 1),
('Bạc xỉu', 'Đồ uống', 25000, 'Nhiều sữa, ít cà phê', 1),
('Trà đào cam sả', 'Đồ uống', 35000, 'Trà trái cây giải khát', 1),
('Trà sữa trân châu', 'Đồ uống', 30000, 'Trà sữa kèm trân châu đen', 1),
('Sinh tố bơ', 'Đồ uống', 35000, 'Sinh tố bơ sáp nguyên chất', 1),
('Nước cam ép', 'Đồ uống', 30000, 'Cam tươi ép nguyên chất', 1),
('Bánh mì que', 'Đồ ăn', 15000, 'Bánh mì que giòn pate', 1),
('Bánh croissant', 'Đồ ăn', 25000, 'Bánh sừng bò bơ Pháp', 1),
('Sandwich gà', 'Đồ ăn', 35000, 'Sandwich gà nướng rau củ', 1);

INSERT INTO ban (so_ban, trang_thai) VALUES
('Bàn 1', 'Trống'),
('Bàn 2', 'Trống'),
('Bàn 3', 'Trống'),
('Bàn 4', 'Trống'),
('Bàn 5', 'Trống'),
('Bàn 6', 'Trống');

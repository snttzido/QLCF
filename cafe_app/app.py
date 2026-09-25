from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
import database as db

app = Flask(__name__)
app.secret_key = 'cafe-quan-ly-secret-key-2026'
STAFF_USERNAME = 'admin'
STAFF_PASSWORD = '123456'
TRANG_THAI_DON = ['Chờ xác nhận', 'Đang chuẩn bị', 'Đã hoàn thành', 'Đã hủy']
PHUONG_THUC_TT = ['Tiền mặt', 'Chuyển khoản']


def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('staff_logged_in'):
            flash('Vui lòng đăng nhập tài khoản nhân viên.', 'error')
            return redirect(url_for('staff_login'))
        return f(*args, **kwargs)
    return decorated_function


# Thông tin ngân hàng dùng để tạo mã QR chuyển khoản (chỉnh lại theo quán thực tế)
BANK_INFO = {
    'ten_ngan_hang': 'Ngân hàng ABC',
    'so_tk': '0123456789',
    'chu_tk': 'QUAN CA PHE',
}


@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if username == STAFF_USERNAME and password == STAFF_PASSWORD:
            session['staff_logged_in'] = True
            flash('Đăng nhập nhân viên thành công.', 'success')
            return redirect(url_for('staff_menu'))

        flash('Sai tên đăng nhập hoặc mật khẩu.', 'error')

    return render_template('staff/login.html')


@app.route('/staff/logout')
def staff_logout():
    session.pop('staff_logged_in', None)
    flash('Đã đăng xuất.', 'success')
    return redirect(url_for('menu'))


@app.before_request
def ensure_cart():
    session.setdefault('cart', [])


@app.context_processor
def inject_current_table():
    ban_id = session.get('ban_id')
    ban_hien_tai = None
    if ban_id:
        ban_hien_tai = db.query('SELECT * FROM ban WHERE id = ?', (ban_id,), one=True)
        if not ban_hien_tai:
            session.pop('ban_id', None)
    return {'ban_hien_tai': ban_hien_tai}


# ---------------------------------------------------------------------------
# QUÉT QR TẠI BÀN
# ---------------------------------------------------------------------------

@app.route('/ban/<int:ban_id>')
def vao_ban(ban_id):
    """Khách quét mã QR dán trên bàn sẽ vào đường link này -> tự động gán bàn cho phiên gọi món."""
    ban = db.query('SELECT * FROM ban WHERE id = ?', (ban_id,), one=True)
    if not ban:
        flash('Mã QR không hợp lệ hoặc bàn không tồn tại.', 'error')
        return redirect(url_for('menu'))
    session['ban_id'] = ban_id
    flash(f'Bạn đang gọi món cho {ban["so_ban"]}. Chúc quý khách ngon miệng!', 'success')
    return redirect(url_for('menu'))


@app.route('/roi-ban')
def roi_ban():
    session.pop('ban_id', None)
    flash('Đã bỏ chọn bàn.', 'success')
    return redirect(url_for('menu'))


# ---------------------------------------------------------------------------
# PHÍA KHÁCH HÀNG
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('menu'))


@app.route('/menu')
def menu():
    mon_list = db.query('SELECT * FROM mon_an WHERE con_ban = 1 ORDER BY loai, ten')
    loai_list = sorted({m['loai'] for m in mon_list})
    return render_template('customer/menu.html', mon_list=mon_list, loai_list=loai_list)


@app.route('/menu/add', methods=['POST'])
def add_to_cart():
    mon_id = request.form.get('mon_id', type=int)
    so_luong = request.form.get(f'so_luong_{mon_id}', default=1, type=int)
    if not mon_id or so_luong is None or so_luong < 1:
        flash('Số lượng không hợp lệ.', 'error')
        return redirect(url_for('menu'))

    mon = db.query('SELECT * FROM mon_an WHERE id = ?', (mon_id,), one=True)
    if not mon:
        flash('Không tìm thấy món này.', 'error')
        return redirect(url_for('menu'))

    cart = session.get('cart', [])
    for item in cart:
        if item['mon_id'] == mon_id:
            item['so_luong'] += so_luong
            break
    else:
        cart.append({'mon_id': mon_id, 'ten': mon['ten'], 'gia': mon['gia'], 'so_luong': so_luong})
    session['cart'] = cart
    flash(f'Đã thêm "{mon["ten"]}" vào giỏ hàng.', 'success')
    return redirect(url_for('menu'))


@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    tong_tien = sum(i['gia'] * i['so_luong'] for i in cart_items)
    ban_trong = db.query("SELECT * FROM ban WHERE trang_thai = 'Trống' ORDER BY so_ban")
    return render_template('customer/cart.html', cart=cart_items, tong_tien=tong_tien, ban_trong=ban_trong)


@app.route('/cart/update/<int:mon_id>', methods=['POST'])
def update_cart(mon_id):
    so_luong = request.form.get('so_luong', type=int)
    cart_items = session.get('cart', [])
    if so_luong and so_luong > 0:
        for item in cart_items:
            if item['mon_id'] == mon_id:
                item['so_luong'] = so_luong
    session['cart'] = cart_items
    flash('Đã cập nhật giỏ hàng.', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:mon_id>', methods=['POST'])
def remove_from_cart(mon_id):
    cart_items = session.get('cart', [])
    cart_items = [i for i in cart_items if i['mon_id'] != mon_id]
    session['cart'] = cart_items
    flash('Đã xóa món khỏi giỏ hàng.', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Giỏ hàng đang trống.', 'error')
        return redirect(url_for('menu'))

    ten_khach = request.form.get('ten_khach', '').strip()
    # Nếu khách vào từ QR của bàn thì luôn dùng bàn đó; nếu không mới dùng lựa chọn trên form (mang đi)
    ban_id = session.get('ban_id') or request.form.get('ban_id', type=int)
    tong_tien = sum(i['gia'] * i['so_luong'] for i in cart_items)
    thoi_gian = datetime.now().strftime('%d/%m/%Y %H:%M')

    don_id = db.execute(
        'INSERT INTO don_hang (ban_id, ten_khach, thoi_gian, trang_thai, da_thanh_toan, tong_tien) '
        "VALUES (?, ?, ?, 'Chờ xác nhận', 0, ?)",
        (ban_id, ten_khach, thoi_gian, tong_tien)
    )
    for item in cart_items:
        db.execute(
            'INSERT INTO chi_tiet_don (don_hang_id, mon_an_id, ten_mon, gia, so_luong) VALUES (?, ?, ?, ?, ?)',
            (don_id, item['mon_id'], item['ten'], item['gia'], item['so_luong'])
        )
    if ban_id:
        db.execute("UPDATE ban SET trang_thai = 'Có khách' WHERE id = ?", (ban_id,))

    session['cart'] = []
    flash(f'Đặt món thành công! Mã đơn #{don_id}. Vui lòng chọn hình thức thanh toán.', 'success')
    return redirect(url_for('order_payment', don_id=don_id))


# ---------------------------------------------------------------------------
# THANH TOÁN PHÍA KHÁCH HÀNG — chọn Tiền mặt / Chuyển khoản
# ---------------------------------------------------------------------------

@app.route('/order/<int:don_id>/payment', methods=['GET', 'POST'])
def order_payment(don_id):
    don = db.query('''SELECT don_hang.*, ban.so_ban FROM don_hang
                       LEFT JOIN ban ON don_hang.ban_id = ban.id
                       WHERE don_hang.id = ?''', (don_id,), one=True)
    if not don:
        flash('Không tìm thấy đơn hàng.', 'error')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        phuong_thuc = request.form.get('phuong_thuc')
        if phuong_thuc not in PHUONG_THUC_TT:
            flash('Vui lòng chọn hình thức thanh toán hợp lệ.', 'error')
        else:
            db.execute('UPDATE don_hang SET phuong_thuc_tt = ? WHERE id = ?', (phuong_thuc, don_id))
        return redirect(url_for('order_payment', don_id=don_id))

    chi_tiet = db.query('SELECT * FROM chi_tiet_don WHERE don_hang_id = ?', (don_id,))
    qr_content = None
    if don['phuong_thuc_tt'] == 'Chuyển khoản':
        noi_dung = f'DH{don_id} {don["ten_khach"] or ""}'.strip()
        qr_content = (
            f'{BANK_INFO["ten_ngan_hang"]}|STK:{BANK_INFO["so_tk"]}|'
            f'Chu TK:{BANK_INFO["chu_tk"]}|So tien:{don["tong_tien"]}|Noi dung:{noi_dung}'
        )
    return render_template(
        'customer/order_payment.html', don=don, chi_tiet=chi_tiet,
        bank=BANK_INFO, qr_content=qr_content
    )


@app.route('/order/<int:don_id>/payment/reset', methods=['POST'])
def order_payment_reset(don_id):
    db.execute('UPDATE don_hang SET phuong_thuc_tt = NULL WHERE id = ?', (don_id,))
    return redirect(url_for('order_payment', don_id=don_id))


# ---------------------------------------------------------------------------
# PHÍA NHÂN VIÊN — Quản lý món
# ---------------------------------------------------------------------------

# THÊM: route này bị thiếu
@app.route('/staff/menu')
@staff_required
def staff_menu():
    mon_list = db.query('SELECT * FROM mon_an ORDER BY loai, ten')
    return render_template('staff/menu_manage.html', mon_list=mon_list)


@app.route('/staff/menu/add', methods=['GET', 'POST'])
@staff_required
def staff_menu_add():
    if request.method == 'POST':
        ten = request.form['ten'].strip()
        loai = request.form['loai']
        gia = request.form.get('gia', type=int, default=0)
        mo_ta = request.form.get('mo_ta', '').strip()
        con_ban = 1 if request.form.get('con_ban') else 0

        if gia < 0 or gia > 10000000:
            flash('Giá món phải từ 0 đến 10.000.000đ.', 'error')
            return render_template('staff/menu_form.html', mon=None)
        if not ten:
            flash('Vui lòng nhập tên món.', 'error')
        else:
            db.execute(
                'INSERT INTO mon_an (ten, loai, gia, mo_ta, con_ban) VALUES (?, ?, ?, ?, ?)',
                (ten, loai, gia, mo_ta, con_ban)
            )
            flash(f'Đã thêm món "{ten}".', 'success')
            return redirect(url_for('staff_menu'))
    return render_template('staff/menu_form.html', mon=None)


@app.route('/staff/menu/edit/<int:mon_id>', methods=['GET', 'POST'])
@staff_required
def staff_menu_edit(mon_id):
    mon = db.query('SELECT * FROM mon_an WHERE id = ?', (mon_id,), one=True)
    if not mon:
        flash('Không tìm thấy món.', 'error')
        return redirect(url_for('staff_menu'))
    if request.method == 'POST':
        ten = request.form['ten'].strip()
        loai = request.form['loai']
        gia = request.form.get('gia', type=int, default=0)
        mo_ta = request.form.get('mo_ta', '').strip()
        con_ban = 1 if request.form.get('con_ban') else 0
        db.execute(
            'UPDATE mon_an SET ten=?, loai=?, gia=?, mo_ta=?, con_ban=? WHERE id=?',
            (ten, loai, gia, mo_ta, con_ban, mon_id)
        )
        flash(f'Đã cập nhật món "{ten}".', 'success')
        return redirect(url_for('staff_menu'))
    return render_template('staff/menu_form.html', mon=mon)


# THÊM: route này để khớp với menu_manage.html
@app.route('/staff/menu/toggle/<int:mon_id>', methods=['POST'])
@staff_required
def staff_menu_toggle(mon_id):
    mon = db.query(
        'SELECT * FROM mon_an WHERE id = ?',
        (mon_id,),
        one=True
    )

    if not mon:
        flash('Không tìm thấy món.', 'error')
        return redirect(url_for('staff_menu'))

    new_status = 0 if mon['con_ban'] else 1

    db.execute(
        'UPDATE mon_an SET con_ban = ? WHERE id = ?',
        (new_status, mon_id)
    )

    if new_status:
        flash(f'Đã mở bán món "{mon["ten"]}".', 'success')
    else:
        flash(f'Đã ngừng bán món "{mon["ten"]}".', 'warning')

    return redirect(url_for('staff_menu'))


@app.route('/staff/menu/delete/<int:mon_id>', methods=['POST'])
@staff_required
def staff_menu_delete(mon_id):

    mon = db.query(
        'SELECT * FROM mon_an WHERE id = ?',
        (mon_id,),
        one=True
    )

    if not mon:
        flash('Không tìm thấy món.', 'error')
        return redirect(url_for('staff_menu'))

    # Kiểm tra món đã từng xuất hiện trong đơn hàng chưa
    da_dat = db.query(
        '''
        SELECT id
        FROM chi_tiet_don
        WHERE mon_an_id = ?
        LIMIT 1
        ''',
        (mon_id,),
        one=True
    )

    if da_dat:
        # Không xóa thật vì món đã có trong lịch sử đơn hàng
        db.execute(
            'UPDATE mon_an SET con_ban = 0 WHERE id = ?',
            (mon_id,)
        )

        flash(
            f'Món "{mon["ten"]}" đã từng có trong đơn hàng nên được chuyển sang "Ngừng bán".',
            'warning'
        )

    else:
        # Chưa từng được đặt -> có thể xóa thật
        db.execute(
            'DELETE FROM mon_an WHERE id = ?',
            (mon_id,)
        )

        flash(
            f'Đã xóa món "{mon["ten"]}".',
            'success'
        )

    return redirect(url_for('staff_menu'))


# ---------------------------------------------------------------------------
# PHÍA NHÂN VIÊN — Quản lý đơn hàng
# ---------------------------------------------------------------------------

@app.route('/staff/orders')
@staff_required
def staff_orders():
    trang_thai = request.args.get('trang_thai')
    sql = '''SELECT don_hang.*, ban.so_ban FROM don_hang
             LEFT JOIN ban ON don_hang.ban_id = ban.id'''
    args = ()
    if trang_thai:
        sql += ' WHERE don_hang.trang_thai = ?'
        args = (trang_thai,)
    sql += ' ORDER BY don_hang.id DESC'
    don_list = db.query(sql, args)
    return render_template('staff/orders.html', don_list=don_list, trang_thai_list=TRANG_THAI_DON, filter_status=trang_thai)


@app.route('/staff/orders/<int:don_id>')
@staff_required
def staff_order_detail(don_id):
    don = db.query('''SELECT don_hang.*, ban.so_ban FROM don_hang
                       LEFT JOIN ban ON don_hang.ban_id = ban.id
                       WHERE don_hang.id = ?''', (don_id,), one=True)
    if not don:
        flash('Không tìm thấy đơn hàng.', 'error')
        return redirect(url_for('staff_orders'))
    chi_tiet = db.query('SELECT * FROM chi_tiet_don WHERE don_hang_id = ?', (don_id,))
    return render_template('staff/order_detail.html', don=don, chi_tiet=chi_tiet, trang_thai_list=TRANG_THAI_DON)


@app.route('/staff/orders/<int:don_id>/status', methods=['POST'])
@staff_required
def staff_order_status(don_id):
    trang_thai = request.form.get('trang_thai')
    if trang_thai not in TRANG_THAI_DON:
        flash('Trạng thái không hợp lệ.', 'error')
        return redirect(url_for('staff_order_detail', don_id=don_id))

    db.execute('UPDATE don_hang SET trang_thai = ? WHERE id = ?', (trang_thai, don_id))

    # Nếu đơn bị hủy hoặc hoàn thành và có bàn, có thể cần cập nhật bàn khi thanh toán xong (xem staff_payment_confirm)
    flash(f'Đã cập nhật trạng thái đơn #{don_id} thành "{trang_thai}".', 'success')
    return redirect(url_for('staff_order_detail', don_id=don_id))


# ---------------------------------------------------------------------------
# PHÍA NHÂN VIÊN — Quản lý bàn
# ---------------------------------------------------------------------------

@app.route('/staff/tables')
@staff_required
def staff_tables():
    ban_list = db.query('SELECT * FROM ban ORDER BY so_ban')
    return render_template('staff/tables.html', ban_list=ban_list)


@app.route('/staff/tables/add', methods=['POST'])
@staff_required
def staff_table_add():
    so_ban = request.form.get('so_ban', '').strip()
    if so_ban:
        db.execute("INSERT INTO ban (so_ban, trang_thai) VALUES (?, 'Trống')", (so_ban,))
        flash(f'Đã thêm {so_ban}.', 'success')
    return redirect(url_for('staff_tables'))


@app.route('/staff/tables/toggle/<int:ban_id>', methods=['POST'])
@staff_required
def staff_table_toggle(ban_id):
    ban = db.query('SELECT * FROM ban WHERE id = ?', (ban_id,), one=True)
    if ban:
        new_status = 'Trống' if ban['trang_thai'] == 'Có khách' else 'Có khách'
        db.execute('UPDATE ban SET trang_thai = ? WHERE id = ?', (new_status, ban_id))
        flash(f'{ban["so_ban"]} đã chuyển sang trạng thái "{new_status}".', 'success')
    return redirect(url_for('staff_tables'))


@app.route('/staff/tables/delete/<int:ban_id>', methods=['POST'])
@staff_required
def staff_table_delete(ban_id):
    db.execute('DELETE FROM ban WHERE id = ?', (ban_id,))
    flash('Đã xóa bàn.', 'success')
    return redirect(url_for('staff_tables'))


@app.route('/staff/tables/<int:ban_id>/qr')
@staff_required
def staff_table_qr(ban_id):
    ban = db.query('SELECT * FROM ban WHERE id = ?', (ban_id,), one=True)
    if not ban:
        flash('Không tìm thấy bàn.', 'error')
        return redirect(url_for('staff_tables'))
    ban_url = url_for('vao_ban', ban_id=ban_id, _external=True)
    return render_template('staff/table_qr_print.html', ban=ban, ban_url=ban_url)


# ---------------------------------------------------------------------------
# PHÍA NHÂN VIÊN — Thanh toán
# ---------------------------------------------------------------------------

@app.route('/staff/payment')
@staff_required
def staff_payment():
    don_list = db.query('''SELECT don_hang.*, ban.so_ban FROM don_hang
                            LEFT JOIN ban ON don_hang.ban_id = ban.id
                            WHERE don_hang.trang_thai = 'Đã hoàn thành' AND don_hang.da_thanh_toan = 0
                            ORDER BY don_hang.id DESC''')
    paid_list = db.query('''SELECT don_hang.*, ban.so_ban FROM don_hang
                             LEFT JOIN ban ON don_hang.ban_id = ban.id
                             WHERE don_hang.da_thanh_toan = 1
                             ORDER BY don_hang.id DESC LIMIT 20''')
    return render_template('staff/payment.html', don_list=don_list, paid_list=paid_list)


@app.route('/staff/payment/<int:don_id>/confirm', methods=['POST'])
@staff_required
def staff_payment_confirm(don_id):
    don = db.query('SELECT * FROM don_hang WHERE id = ?', (don_id,), one=True)
    if not don:
        flash('Không tìm thấy đơn hàng.', 'error')
        return redirect(url_for('staff_payment'))
    db.execute('UPDATE don_hang SET da_thanh_toan = 1 WHERE id = ?', (don_id,))
    if don['ban_id']:
        db.execute("UPDATE ban SET trang_thai = 'Trống' WHERE id = ?", (don['ban_id'],))
    flash(f'Đã xác nhận thanh toán đơn #{don_id}.', 'success')
    return redirect(url_for('staff_payment'))


if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
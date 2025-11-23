"""
H&M HEALTH SHOP - Phiên bản đơn giản
File này chứa TẤT CẢ code: database, routes, logic
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import shortuuid  # Package Python để tạo mã đơn hàng
from dateutil import parser  # Package Python để xử lý date

# ============================================
# PHẦN 1: KHỞI TẠO ỨNG DỤNG
# ============================================

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Cần cho session và flash messages

DATABASE = 'database.db'  # File database SQLite


# ============================================
# PHẦN 2: HÀM XỬ LÝ DATABASE
# ============================================

def get_db_connection():
    """
    Hàm kết nối database SQLite
    
    Returns:
        sqlite3.Connection: Kết nối database
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột bằng tên
    return conn


def init_db():
    """
    Hàm khởi tạo database và tạo các bảng
    Chỉ chạy 1 lần khi bắt đầu
    """
    conn = get_db_connection()
    
    # Tạo bảng danh mục sản phẩm
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Tạo bảng sản phẩm
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            discount_price REAL,
            stock INTEGER DEFAULT 0,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Tạo bảng đơn hàng
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'cod',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tạo bảng chi tiết đơn hàng
    conn.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database đã được khởi tạo!")


def seed_sample_data():
    """
    Hàm thêm dữ liệu mẫu vào database
    """
    conn = get_db_connection()
    
    # Kiểm tra đã có dữ liệu chưa
    existing = conn.execute('SELECT COUNT(*) as count FROM categories').fetchone()
    if existing['count'] > 0:
        print("⚠️ Dữ liệu mẫu đã tồn tại!")
        conn.close()
        return
    
    # Thêm danh mục
    categories = [
        ('Thực phẩm chức năng', 'Vitamin, khoáng chất, bổ sung dinh dưỡng'),
        ('Thiết bị y tế', 'Máy đo huyết áp, nhiệt kế, máy massage'),
        ('Sức khỏe tim mạch', 'Hỗ trợ tim mạch, huyết áp'),
        ('Sức khỏe xương khớp', 'Canxi, glucosamine, collagen'),
    ]
    
    for cat in categories:
        conn.execute('INSERT INTO categories (name, description) VALUES (?, ?)', cat)
    
    # Thêm sản phẩm
    products = [
        (1, 'Viên rau củ Kera', 'Kera gồm 22 nguyên liệu, trong đó 10 loại bột rau củ quả, chiếm tỉ lệ 28,43% nguyên liệu được đưa vào sản xuất. Cụ thể: bột cải bó xôi (5,63%), bột rau má (4,69%), bột chùm ngây (3,75%), bột diếp cá (3,12%), bột cần tây (2,5%), bột chuối xanh (2,19%), bột cà rốt (1,56%), bột bí ngô (1,56%), bột khoai lang tím (1,56%) và bột tảo xanh (1,56%).', 135000, 119000, 100, 'https://cdn2.tuoitre.vn/thumb_w/480/471584752817336320/2025/3/8/4739917721221122077466932691126678254958579118n-17414199877212052247848.jpg'),
        (1, 'Omega 3 Fish Oil', 'Hỗ trợ tim mạch và não bộ', 350000, 299000, 80, 'https://cdn.nhathuoclongchau.com.vn/unsafe/636x0/filters:quality(90)/DSC_05151_0c39e73eec.png'),
        (2, 'Máy đo huyết áp Omron', 'Đo huyết áp tự động, chính xác', 850000, 799000, 50, 'https://cdn.nhathuoclongchau.com.vn/unsafe/636x0/filters:quality(90)/60836162e571302f69604_b4a0d8f19f.jpg'),
        (3, 'CoQ10 - Hỗ trợ tim mạch', 'Tăng cường sức khỏe tim mạch', 450000, 399000, 60, 'hhttps://cdn.nhathuoclongchau.com.vn/unsafe/636x0/filters:quality(90)/00033382_vien_uong_ho_tro_tim_mach_heart_ace_support_vitamins_for_life_30v_9384_63e1_large_9a7ec569a1.jpg'),
        (4, 'Canxi + D3', 'Xương chắc khỏe, phòng loãng xương', 180000, 149000, 120, 'https://cdn.nhathuoclongchau.com.vn/unsafe/636x0/filters:quality(90)/DSC_04864_8b87847a4a.jpg'),
        (1, 'Men vi sinh Probiotics', 'Cân bằng hệ vi sinh đường ruột', 320000, 279000, 90, 'https://cdn.nhathuoclongchau.com.vn/unsafe/636x0/filters:quality(90)/00020291_probiotics_lactomin_plus_30_goi_mebiphar_4889_5cec_large_c6ec22bbd7.jpg'),
    ]
    
    for prod in products:
        conn.execute('''
            INSERT INTO products (category_id, name, description, price, discount_price, stock, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', prod)
    
    conn.commit()
    conn.close()
    print("✅ Dữ liệu mẫu đã được thêm!")


# ============================================
# PHẦN 3: HÀM TIỆN ÍCH
# ============================================

def get_cart():
    """
    Lấy giỏ hàng từ session
    Session là nơi lưu trữ tạm thời trên trình duyệt
    
    Returns:
        list: Danh sách sản phẩm trong giỏ hàng
    """
    return session.get('cart', [])


def save_cart(cart):
    """
    Lưu giỏ hàng vào session
    
    Args:
        cart (list): Danh sách sản phẩm trong giỏ hàng
    """
    session['cart'] = cart


def calculate_cart_total(cart):
    """
    Tính tổng tiền giỏ hàng
    
    Args:
        cart (list): Danh sách sản phẩm trong giỏ hàng
        
    Returns:
        float: Tổng tiền
    """
    total = 0
    for item in cart:
        total += item['price'] * item['quantity']
    return total


def format_price(price):
    """
    Format giá tiền theo định dạng Việt Nam
    
    Args:
        price (float): Giá tiền
        
    Returns:
        str: Giá đã format (vd: 250.000₫)
    """
    return f"{int(price):,}₫".replace(',', '.')


# Đăng ký filter cho template
app.jinja_env.filters['format_price'] = format_price


# ============================================
# PHẦN 4: ROUTES - XỬ LÝ CÁC TRANG WEB
# ============================================

@app.route('/')
def index():
    """
    Trang chủ - Hiển thị sản phẩm nổi bật
    
    URL: http://localhost:5000/
    """
    conn = get_db_connection()
    
    # Lấy tất cả danh mục
    categories = conn.execute('SELECT * FROM categories').fetchall()
    
    # Lấy 6 sản phẩm mới nhất
    products = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
        LIMIT 6
    ''').fetchall()
    
    conn.close()
    
    # Đếm số sản phẩm trong giỏ hàng
    cart = get_cart()
    cart_count = len(cart)
    
    return render_template('index.html', 
                         categories=categories, 
                         products=products,
                         cart_count=cart_count)


@app.route('/products')
def products():
    """
    Trang danh sách sản phẩm
    
    URL: http://localhost:5000/products
    URL: http://localhost:5000/products?category=1
    """
    conn = get_db_connection()
    
    # Lấy tham số category từ URL (nếu có)
    category_id = request.args.get('category', type=int)
    
    # Lấy tất cả danh mục
    categories = conn.execute('SELECT * FROM categories').fetchall()
    
    # Query sản phẩm theo danh mục (nếu có)
    if category_id:
        products = conn.execute('''
            SELECT p.*, c.name as category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.category_id = ?
            ORDER BY p.created_at DESC
        ''', (category_id,)).fetchall()
        
        current_category = conn.execute('SELECT * FROM categories WHERE id = ?', 
                                       (category_id,)).fetchone()
    else:
        products = conn.execute('''
            SELECT p.*, c.name as category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC
        ''').fetchall()
        current_category = None
    
    conn.close()
    
    cart_count = len(get_cart())
    
    return render_template('products.html',
                         categories=categories,
                         products=products,
                         current_category=current_category,
                         cart_count=cart_count)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    Trang chi tiết sản phẩm
    
    URL: http://localhost:5000/product/1
    
    Args:
        product_id (int): ID của sản phẩm
    """
    conn = get_db_connection()
    
    # Lấy thông tin sản phẩm
    product = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (product_id,)).fetchone()
    
    if not product:
        conn.close()
        flash('Không tìm thấy sản phẩm!', 'error')
        return redirect(url_for('products'))
    
    # Lấy sản phẩm liên quan (cùng danh mục)
    related_products = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ?
        LIMIT 4
    ''', (product['category_id'], product_id)).fetchall()
    
    conn.close()
    
    cart_count = len(get_cart())
    
    return render_template('product_detail.html',
                         product=product,
                         related_products=related_products,
                         cart_count=cart_count)


@app.route('/cart')
def cart():
    """
    Trang giỏ hàng
    
    URL: http://localhost:5000/cart
    """
    cart_items = get_cart()
    cart_total = calculate_cart_total(cart_items)
    cart_count = len(cart_items)
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         cart_total=cart_total,
                         cart_count=cart_count)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """
    Thêm sản phẩm vào giỏ hàng
    
    URL: POST http://localhost:5000/cart/add/1
    
    Args:
        product_id (int): ID của sản phẩm cần thêm
    """
    conn = get_db_connection()
    
    # Lấy thông tin sản phẩm từ database
    product = conn.execute('SELECT * FROM products WHERE id = ?', 
                          (product_id,)).fetchone()
    conn.close()
    
    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('products'))
    
    # Kiểm tra còn hàng không
    if product['stock'] <= 0:
        flash('Sản phẩm đã hết hàng!', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Lấy số lượng từ form (mặc định là 1)
    quantity = request.form.get('quantity', 1, type=int)
    
    # Kiểm tra số lượng hợp lệ
    if quantity > product['stock']:
        flash(f'Chỉ còn {product["stock"]} sản phẩm trong kho!', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Lấy giỏ hàng hiện tại
    cart = get_cart()
    
    # Kiểm tra sản phẩm đã có trong giỏ chưa
    found = False
    for item in cart:
        if item['id'] == product_id:
            # Nếu có rồi thì tăng số lượng
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        # Nếu chưa có thì thêm mới
        # Sử dụng discount_price nếu có, không thì dùng price
        price = product['discount_price'] if product['discount_price'] else product['price']
        
        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': price,
            'quantity': quantity,
            'image_url': product['image_url']
        })
    
    # Lưu giỏ hàng vào session
    save_cart(cart)
    
    flash(f'Đã thêm "{product["name"]}" vào giỏ hàng!', 'success')
    return redirect(request.referrer or url_for('products'))


@app.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng
    
    URL: POST http://localhost:5000/cart/update/1
    
    Args:
        product_id (int): ID của sản phẩm cần cập nhật
    """
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity <= 0:
        return redirect(url_for('remove_from_cart', product_id=product_id))
    
    cart = get_cart()
    
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] = quantity
            break
    
    save_cart(cart)
    flash('Đã cập nhật giỏ hàng!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    """
    Xóa sản phẩm khỏi giỏ hàng
    
    URL: GET http://localhost:5000/cart/remove/1
    
    Args:
        product_id (int): ID của sản phẩm cần xóa
    """
    cart = get_cart()
    
    # Lọc bỏ sản phẩm cần xóa
    cart = [item for item in cart if item['id'] != product_id]
    
    save_cart(cart)
    flash('Đã xóa sản phẩm khỏi giỏ hàng!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/clear')
def clear_cart():
    """
    Xóa toàn bộ giỏ hàng
    
    URL: GET http://localhost:5000/cart/clear
    """
    session['cart'] = []
    flash('Đã xóa toàn bộ giỏ hàng!', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """
    Trang thanh toán
    
    URL: GET/POST http://localhost:5000/checkout
    """
    cart_items = get_cart()
    
    # Kiểm tra giỏ hàng có trống không
    if not cart_items:
        flash('Giỏ hàng trống! Vui lòng thêm sản phẩm.', 'warning')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        # Lấy thông tin từ form
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_address = request.form.get('customer_address', '').strip()
        payment_method = request.form.get('payment_method', 'cod')
        note = request.form.get('note', '').strip()
        
        # Validate dữ liệu
        if not customer_name or not customer_phone or not customer_address:
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            cart_total = calculate_cart_total(cart_items)
            return render_template('checkout.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total,
                                 cart_count=len(cart_items))
        
        # Tạo mã đơn hàng duy nhất bằng shortuuid (package Python)
        order_code = 'HM' + shortuuid.ShortUUID().random(length=8).upper()
        
        # Tính tổng tiền
        total_amount = calculate_cart_total(cart_items)
        
        # Lưu đơn hàng vào database
        conn = get_db_connection()
        
        try:
            # Thêm đơn hàng
            cursor = conn.execute('''
                INSERT INTO orders (order_code, customer_name, customer_phone, customer_address, 
                                  total_amount, payment_method, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_code, customer_name, customer_phone, customer_address,
                  total_amount, payment_method, note))
            
            order_id = cursor.lastrowid
            
            # Thêm chi tiết đơn hàng
            for item in cart_items:
                conn.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (order_id, item['id'], item['name'], item['price'], 
                     item['quantity'], item['price'] * item['quantity']))
                
                # Giảm số lượng tồn kho
                conn.execute('''
                    UPDATE products 
                    SET stock = stock - ?
                    WHERE id = ?
                ''', (item['quantity'], item['id']))
            
            conn.commit()
            
            # Xóa giỏ hàng
            session['cart'] = []
            
            flash(f'Đặt hàng thành công! Mã đơn hàng: {order_code}', 'success')
            return redirect(url_for('order_success', order_code=order_code))
            
        except Exception as e:
            conn.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        finally:
            conn.close()
    
    # GET request - hiển thị form
    cart_total = calculate_cart_total(cart_items)
    return render_template('checkout.html',
                         cart_items=cart_items,
                         cart_total=cart_total,
                         cart_count=len(cart_items))


@app.route('/order/<order_code>')
def order_success(order_code):
    """
    Trang xác nhận đơn hàng thành công
    
    URL: http://localhost:5000/order/HM12345678
    
    Args:
        order_code (str): Mã đơn hàng
    """
    conn = get_db_connection()
    
    # Lấy thông tin đơn hàng
    order = conn.execute('SELECT * FROM orders WHERE order_code = ?', 
                        (order_code,)).fetchone()
    
    if not order:
        conn.close()
        flash('Không tìm thấy đơn hàng!', 'error')
        return redirect(url_for('index'))
    
    # Lấy chi tiết đơn hàng
    order_items = conn.execute('''
        SELECT * FROM order_items WHERE order_id = ?
    ''', (order['id'],)).fetchall()
    
    conn.close()
    
    return render_template('order_success.html',
                         order=order,
                         order_items=order_items)


@app.route('/search')
def search():
    """
    Tìm kiếm sản phẩm
    
    URL: http://localhost:5000/search?q=vitamin
    """
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return redirect(url_for('products'))
    
    conn = get_db_connection()
    
    # Tìm kiếm sản phẩm theo tên
    products = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.name LIKE ? OR p.description LIKE ?
        ORDER BY p.created_at DESC
    ''', (f'%{keyword}%', f'%{keyword}%')).fetchall()
    
    categories = conn.execute('SELECT * FROM categories').fetchall()
    
    conn.close()
    
    cart_count = len(get_cart())
    
    return render_template('products.html',
                         categories=categories,
                         products=products,
                         current_category=None,
                         keyword=keyword,
                         cart_count=cart_count)


# ============================================
# PHẦN 5: CHẠY ỨNG DỤNG
# ============================================

if __name__ == '__main__':
    # Khởi tạo database
    init_db()
    seed_sample_data()
    
    # Lấy PORT từ environment variable (cho Render)
    import os
    port = int(os.environ.get('PORT', 5000))
    
    # Chạy ứng dụng
    app.run(host='0.0.0.0', port=port)
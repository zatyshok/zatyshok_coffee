from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from config import Config
from models import db, Category, Product, User, Order, OrderItem
from functools import wraps
from datetime import timedelta
import requests
import json

# ініціалізація додатку
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# налаштування gemini api
try:
    import google.generativeai as genai
    genai.configure(api_key=app.config['GEMINI_API_KEY'])
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

@app.before_request
def make_session_permanent():
    session.permanent = True

# декоратори для перевірки прав доступу
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступу до цієї сторінки необхідно увійти в акаунт.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Доступ заборонено.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# допоміжні функції
def get_weather_temp():
    """Отримує поточну температуру через Open-Meteo API (безкоштовно)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={app.config['WEATHER_LAT']}"
            f"&longitude={app.config['WEATHER_LON']}"
            f"&current_weather=true"
        )
        resp = requests.get(url, timeout=3)
        data = resp.json()
        return data['current_weather']['temperature']
    except Exception:
        return None


def get_cart():
    """Повертає кошик з сесії."""
    return session.get('cart', {})


def cart_total(cart):
    return sum(item['price'] * item['quantity'] for item in cart.values())


def build_chatbot_prompt(user_message: str, history: list = None) -> str:
    """Формує промпт для Gemini з контекстом меню та історією."""
    products = Product.query.filter_by(available=True).all()
    menu_lines = []
    for p in products:
        allergen_info = f", алергени: {p.allergens}" if p.allergens else ""
        menu_lines.append(
            f"- {p.name} ({p.category.name}): {p.description}, "
            f"ціна {p.price:.0f} грн{allergen_info}"
        )
    menu_text = "\n".join(menu_lines)

    history_text = ""
    if history and len(history) > 0:
        history_text = "\nІсторія діалогу:\n"
        for msg in history[-4:]: # беремо останні 4 повідомлення
            role = "Гість" if msg.get('type') == 'user' else "Ти (Асистент)"
            history_text += f"{role}: {msg.get('text')}\n"

    return f"""Ти — AI-асистент кав'ярні «Затишок» у Львові.
Твоє завдання — допомагати гостям обирати страви та напої, відповідати на питання про склад і алергени, а також приймати замовлення через чат.

Актуальне меню:
{menu_text}

Правила відповіді:
1. Відповідай виключно українською мовою.
2. Будь дружнім, але лаконічним — 1–4 речення.
3. Не вітайся кожного разу, якщо в історії діалогу вже є твоє привітання.
4. Якщо гість цікавиться стравою чи напоєм — розкажи про нього і запитай: "Бажаєте, щоб я додав це до вашого кошика?".
5. Якщо гість просить додати кілька товарів, обов'язково перелічуй їх через кому. Формат команди в кінці відповіді має бути такий: ЗАМОВЛЕННЯ: [Назва 1], [Назва 2].
6. КРИТИЧНО ВАЖЛИВО: Пиши команду ЗАМОВЛЕННЯ: ... ЛИШЕ ОДИН РАЗ для кожної страви — рівно в той момент, коли ти погоджуєшся її додати. Ніколи не дублюй цю команду в наступних повідомленнях!
7. Не вигадуй страв, яких немає в меню.
{history_text}
Запит гостя: {user_message}"""


# публічні сторінки (головна, меню, про нас)
@app.route('/')
def index():
    popular = Product.query.filter_by(available=True, is_popular=True).limit(6).all()
    temp = get_weather_temp()
    if temp is not None:
        if temp >= 18:
            weather_drinks = Product.query.filter_by(available=True, is_cold=True).limit(4).all()
            weather_label = f'Спекотно ({temp:.0f}°C) — рекомендуємо холодне'
        else:
            weather_drinks = Product.query.filter_by(available=True, is_cold=False).limit(4).all()
            weather_label = f'Прохолодно ({temp:.0f}°C) — рекомендуємо гаряче'
    else:
        weather_drinks = []
        weather_label = None
    cart = get_cart()
    return render_template(
        'index.html',
        popular=popular,
        weather_drinks=weather_drinks,
        weather_label=weather_label,
        cart_count=sum(i['quantity'] for i in cart.values()),
    )


@app.route('/menu')
def menu():
    categories = Category.query.all()
    selected = request.args.get('category', 'all')
    if selected == 'all':
        products = Product.query.filter_by(available=True).all()
    else:
        cat = Category.query.filter_by(slug=selected).first_or_404()
        products = Product.query.filter_by(category_id=cat.id, available=True).all()
    cart = get_cart()
    return render_template(
        'menu.html',
        categories=categories,
        products=products,
        selected=selected,
        cart_count=sum(i['quantity'] for i in cart.values()),
    )


@app.route('/about')
def about():
    cart = get_cart()
    return render_template(
        'about.html',
        cart_count=sum(i['quantity'] for i in cart.values()),
    )


# маршрути для входу та реєстрації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Ласкаво просимо, {user.name}!', 'success')
            return redirect(url_for('index'))
        flash('Невірна електронна адреса або пароль.', 'danger')
    return render_template('login.html', mode='login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not name or not email or not password:
            flash('Заповніть усі поля.', 'danger')
        elif password != confirm:
            flash('Паролі не збігаються.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Акаунт з такою адресою вже існує.', 'danger')
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Реєстрація успішна! Ласкаво просимо, {name}!', 'success')
            return redirect(url_for('index'))
    return render_template('login.html', mode='register')


@app.route('/logout')
def logout():
    session.clear()
    flash('Ви вийшли з акаунту.', 'info')
    return redirect(url_for('index'))


# особистий кабінет користувача
@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    cart = get_cart()
    return render_template(
        'profile.html',
        user=user,
        orders=orders,
        cart_count=sum(i['quantity'] for i in cart.values()),
    )


# сторінка кошика
@app.route('/cart')
def cart():
    cart_data = get_cart()
    cart = get_cart()
    return render_template(
        'cart.html',
        cart=cart_data,
        total=cart_total(cart_data),
        cart_count=sum(i['quantity'] for i in cart.values()),
    )


# api для роботи з кошиком
@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    product = Product.query.get(int(product_id))
    if not product or not product.available:
        return jsonify({'error': 'Товар недоступний'}), 404
    cart = session.get('cart', {})
    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': product.price,
            'quantity': 1,
        }
    session['cart'] = cart
    session.modified = True
    total_count = sum(i['quantity'] for i in cart.values())
    return jsonify({'success': True, 'cart_count': total_count})


@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    cart = session.get('cart', {})
    if product_id in cart:
        if cart[product_id]['quantity'] > 1:
            cart[product_id]['quantity'] -= 1
        else:
            del cart[product_id]
    session['cart'] = cart
    session.modified = True
    return jsonify({
        'success': True,
        'cart_count': sum(i['quantity'] for i in cart.values()),
        'total': cart_total(cart),
    })


@app.route('/api/cart/clear', methods=['POST'])
def api_cart_clear():
    session['cart'] = {}
    session.modified = True
    return jsonify({'success': True})


# api для оформлення та перевірки замовлень
@app.route('/api/order', methods=['POST'])
def api_place_order():
    cart = session.get('cart', {})
    if not cart:
        return jsonify({'error': 'Кошик порожній'}), 400
    data = request.get_json() or {}
    comment = data.get('comment', '')
    user_id = session.get('user_id')
    guest_name = data.get('guest_name', 'Гість') if not user_id else None

    total = cart_total(cart)
    order = Order(user_id=user_id, guest_name=guest_name, total=total, comment=comment)
    db.session.add(order)
    db.session.flush()

    for pid, item in cart.items():
        oi = OrderItem(
            order_id=order.id,
            product_id=int(pid),
            quantity=item['quantity'],
            price_at_order=item['price'],
        )
        db.session.add(oi)

    db.session.commit()
    session['cart'] = {}
    session.modified = True
    return jsonify({'success': True, 'order_id': order.id})


@app.route('/api/order-status/<int:order_id>')
def api_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'status': order.status, 'order_id': order.id})


# api для отримання меню у форматі json (для чатботу)
@app.route('/api/menu')
def api_menu():
    products = Product.query.filter_by(available=True).all()
    return jsonify([p.to_dict() for p in products])


# api для запитів до чатботу
@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    data = request.get_json()
    user_message = (data.get('message') or '').strip()
    history = data.get('history', [])
    
    if not user_message:
        return jsonify({'error': 'Порожнє повідомлення'}), 400

    if not GEMINI_AVAILABLE or app.config['GEMINI_API_KEY'] == 'YOUR_GEMINI_API_KEY_HERE':
        return jsonify({
            'reply': "AI-асистент тимчасово недоступний. Зверніться до персоналу кав'ярні."
        })

    try:
        prompt = build_chatbot_prompt(user_message, history)
        response = gemini_model.generate_content(prompt)
        reply = response.text.strip()

        order_items = []
        cart_updated = False
        if 'ЗАМОВЛЕННЯ:' in reply:
            try:
                # Відокремлюємо видиму частину відповіді від технічної команди
                parts = reply.split('ЗАМОВЛЕННЯ:')
                visible_reply = parts[0].strip()
                order_part = parts[1]
                
                # Розділяємо по комах або союзах "та", "і"
                import re
                raw_items = re.split(r',|\s+і\s+|\s+та\s+', order_part)
                cart = session.get('cart', {})
                
                for item_name in raw_items:
                    # Очищаємо від пробілів, дужок та крапок
                    item_name = re.sub(r'[\[\]\.\n]', '', item_name).strip()
                    if not item_name: continue
                    # Шукаємо товар у базі
                    product = Product.query.filter(Product.name.ilike(f"%{item_name}%")).first()
                    if product and product.available:
                        pid = str(product.id)
                        if pid in cart:
                            cart[pid]['quantity'] += 1
                        else:
                            cart[pid] = {'name': product.name, 'price': product.price, 'quantity': 1}
                        order_items.append(product.name)
                        cart_updated = True
                
                if cart_updated:
                    session['cart'] = cart
                    session.modified = True
                
                reply = visible_reply # не показуємо "ЗАМОВЛЕННЯ: [...]" юзеру
            except Exception as e:
                print("Order parse error:", e)

        total_count = sum(i['quantity'] for i in session.get('cart', {}).values())
        return jsonify({
            'reply': reply, 
            'order_items': order_items,
            'cart_count': total_count
        })
    except Exception as e:
        with open('chatbot_error.log', 'w', encoding='utf-8') as f:
            f.write(str(e))
        return jsonify({'reply': 'Виникла помилка при обробці запиту. Спробуйте ще раз.'})


# адмін-панель: статистика, замовлення, меню
@app.route('/admin')
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    stats = {
        'total_orders': Order.query.count(),
        'active_orders': Order.query.filter(Order.status.in_(['Прийнято', 'Готується'])).count(),
        'total_products': Product.query.count(),
        'total_users': User.query.filter_by(role='user').count(),
    }
    return render_template('admin/dashboard.html', orders=orders, stats=stats)


@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    allowed = ['Прийнято', 'Готується', 'Готове', 'Видано']
    if new_status in allowed:
        order.status = new_status
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/menu')
@admin_required
def admin_menu():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/menu_edit.html', products=products, categories=categories)


@app.route('/admin/menu/add', methods=['POST'])
@admin_required
def admin_menu_add():
    p = Product(
        name=request.form['name'],
        description=request.form['description'],
        price=float(request.form['price']),
        category_id=int(request.form['category_id']),
        allergens=request.form.get('allergens', ''),
        is_popular='is_popular' in request.form,
        is_cold='is_cold' in request.form,
    )
    db.session.add(p)
    db.session.commit()
    flash('Позицію додано.', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:product_id>/toggle', methods=['POST'])
@admin_required
def admin_menu_toggle(product_id):
    p = Product.query.get_or_404(product_id)
    p.available = not p.available
    db.session.commit()
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_menu_delete(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash('Позицію видалено.', 'success')
    return redirect(url_for('admin_menu'))


# запуск сервера
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # host='0.0.0.0' — сайт доступний у локальній мережі з будь-якого пристрою
    app.run(debug=True, host='0.0.0.0', port=5000)

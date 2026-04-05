"""
seed_db.py — наповнення бази даних тестовими даними.
Запуск: py seed_db.py
"""
from app import app, db
from models import Category, Product, User, Order, OrderItem

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── Категорії ────────────────────────────────────────────────────────
        cats = [
            Category(name='Гарячі напої', slug='hot',     icon='☕'),
            Category(name='Холодні напої', slug='cold',    icon='🧊'),
            Category(name='Десерти',       slug='desserts', icon='🍰'),
            Category(name='Снеки',         slug='snacks',   icon='🥐'),
        ]
        db.session.add_all(cats)
        db.session.flush()
        hot, cold, desserts, snacks = cats

        # ── Продукти ─────────────────────────────────────────────────────────
        products = [
            # Гарячі
            Product(name='Еспресо',         description='Класична подвійна порція арабіки з насиченим смаком і кремовою пінкою',          price=45,  category_id=hot.id,      is_popular=True,  allergens=''),
            Product(name='Американо',       description='М\'який еспресо, розведений гарячою водою — ідеальний ранковий вибір',           price=55,  category_id=hot.id,      allergens=''),
            Product(name='Капучино',        description='Еспресо з оксамитовим молочним мікропіною у пропорції 1:1:1',                    price=75,  category_id=hot.id,      is_popular=True,  allergens='молоко'),
            Product(name='Лате',            description='Ніжний кавовий напій з великою кількістю спіненого молока',                      price=85,  category_id=hot.id,      is_popular=True,  allergens='молоко'),
            Product(name='Флет Уайт',       description='Концентрований кавовий смак із невеликим шаром мікропіни — вибір цінителів',     price=80,  category_id=hot.id,      allergens='молоко'),
            Product(name='Раф',             description='Еспресо, збиті вершки та ванільний цукор — оксамитова текстура',                  price=95,  category_id=hot.id,      allergens='молоко'),
            Product(name='Матча Лате',      description='Японський зелений чай матча зі спіненим молоком — м\'який і ароматний',           price=95,  category_id=hot.id,      allergens='молоко'),
            Product(name='Гарячий шоколад', description='Насичений бельгійський какао з молоком і вершковою піною',                       price=80,  category_id=hot.id,      allergens='молоко, какао'),
            # Холодні
            Product(name='Айс Лате',        description='Еспресо з молоком і льодом — освіжаючий і бадьорий',                             price=90,  category_id=cold.id,     is_popular=True,  is_cold=True, allergens='молоко'),
            Product(name='Колд Брю',        description='Кава холодного заварювання 18 годин — м\'яка та без кислотності',                 price=85,  category_id=cold.id,     is_cold=True,     allergens=''),
            Product(name='Фрапе',           description='Збитий охолоджений кавовий напій з молоком і льодом',                            price=95,  category_id=cold.id,     is_popular=True,  is_cold=True, allergens='молоко'),
            Product(name='Айс Американо',   description='Подвійний еспресо з холодною водою та льодом',                                   price=65,  category_id=cold.id,     is_cold=True,     allergens=''),
            Product(name='Лимонад Базилік-Лайм', description='Домашній лимонад на основі свіжого базиліку та соку лайма',               price=80,  category_id=cold.id,     is_cold=True,     allergens=''),
            # Десерти
            Product(name='Чізкейк',         description='Класичний нью-йоркський чізкейк на основі вершкового сиру та печива',            price=110, category_id=desserts.id, is_popular=True,  allergens='глютен, молоко, яйця'),
            Product(name='Тірамісу',        description='Традиційний італійський десерт із маскарпоне, еспресо та савоярді',             price=115, category_id=desserts.id, allergens='глютен, молоко, яйця'),
            Product(name='Бельгійська вафля',description='Хрустка вафля з ягодами та збитими вершками',                                  price=95,  category_id=desserts.id, is_popular=True,  allergens='глютен, молоко, яйця'),
            Product(name='Шоколадний брауні',description='Щільний вологий брауні з бельгійського чорного шоколаду',                      price=85,  category_id=desserts.id, allergens='глютен, молоко, яйця, какао'),
            Product(name='Медівник',        description='Традиційний карпатський медівник із ніжними шарами та медовим кремом',           price=90,  category_id=desserts.id, allergens='глютен, молоко, яйця, мед'),
            # Снеки
            Product(name='Круасан масляний',description='Класичний французький круасан із вершковим маслом — хрусткий зовні та ніжний всередині', price=65, category_id=snacks.id, allergens='глютен, молоко'),
            Product(name='Круасан з шоколадом', description='Маслений круасан із начинкою з темного бельгійського шоколаду',             price=75,  category_id=snacks.id,   allergens='глютен, молоко, какао'),
            Product(name='Сендвіч з лососем',description='Цільнозерновий хліб, вершковий сир, малосольний лосось, каперси',              price=145, category_id=snacks.id,   allergens='глютен, молоко, риба'),
            Product(name='Тост авокадо-яйце',description='Підсмажений хліб з авокадо-пюре, яйцем пашот і мікрогрином',                  price=130, category_id=snacks.id,   allergens='глютен, яйця'),
            Product(name='Кіш лотарінзький',description='Відкритий пиріг із шинкою, сиром і яєчно-вершковою заливкою',                  price=120, category_id=snacks.id,   allergens='глютен, молоко, яйця'),
        ]
        db.session.add_all(products)

        # ── Користувачі ──────────────────────────────────────────────────────
        admin = User(name='Адміністратор', email='admin@zatyshok.ua', role='admin')
        admin.set_password('admin123')
        user1 = User(name='Тестовий Користувач', email='user@zatyshok.ua')
        user1.set_password('user123')
        db.session.add_all([admin, user1])
        db.session.flush()

        # ── Тестове замовлення ───────────────────────────────────────────────
        order = Order(user_id=user1.id, total=160, status='Готується', comment='Без цукру')
        db.session.add(order)
        db.session.flush()
        db.session.add_all([
            OrderItem(order_id=order.id, product_id=products[2].id, quantity=1, price_at_order=75),
            OrderItem(order_id=order.id, product_id=products[13].id, quantity=1, price_at_order=110),
        ])

        db.session.commit()
        print('✅ Базу даних наповнено успішно!')
        print('   Адмін: admin@zatyshok.ua / admin123')
        print('   Користувач: user@zatyshok.ua / user123')

if __name__ == '__main__':
    seed()

/* main.js — загальна логіка: гамбургер, кошик, кнопки "Додати" */

// гамбургер меню для мобільних
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('nav-links');

hamburger?.addEventListener('click', () => {
  const open = hamburger.getAttribute('aria-expanded') === 'true';
  hamburger.setAttribute('aria-expanded', String(!open));
  navLinks.classList.toggle('nav--open', !open);
});

// Закрити меню при кліку поза ним
document.addEventListener('click', e => {
  if (!hamburger?.contains(e.target) && !navLinks?.contains(e.target)) {
    hamburger?.setAttribute('aria-expanded', 'false');
    navLinks?.classList.remove('nav--open');
  }
});

// обробка натискання на кнопки "додати до кошика"
document.addEventListener('click', async e => {
  const btn = e.target.closest('.add-to-cart');
  if (!btn) return;

  const productId = btn.dataset.id;
  btn.disabled = true;
  btn.textContent = '✓';

  try {
    const res = await fetch('/api/cart/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId }),
    });
    const data = await res.json();
    if (data.success) {
      updateCartBadge(data.cart_count);
      btn.textContent = '✓ Додано';
      btn.classList.add('btn--success');
      setTimeout(() => {
        btn.textContent = '+ Додати';
        btn.classList.remove('btn--success');
        btn.disabled = false;
      }, 1500);
    }
  } catch {
    btn.textContent = '+ Додати';
    btn.disabled = false;
  }
});

// функція для оновлення лічильника товарів в кошику
function updateCartBadge(count) {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  badge.textContent = count;
  badge.classList.toggle('hidden', count === 0);
  badge.classList.add('bump');
  setTimeout(() => badge.classList.remove('bump'), 300);
}

// закриваємо повідомлення через 4 секунди автоматично
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.remove(), 4000);
});

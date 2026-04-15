/* chatbot.js — логіка AI-чатботу (Gemini API через Flask backend) */

const toggle   = document.getElementById('chatbot-toggle');
const window_  = document.getElementById('chatbot-window');
const closeBtn = document.getElementById('chatbot-close');
const input    = document.getElementById('chatbot-input');
const sendBtn  = document.getElementById('chatbot-send');
const messages = document.getElementById('chatbot-messages');

// функції для відкриття та закриття вікна чатботу
toggle?.addEventListener('click', () => {
  window_?.classList.toggle('chatbot--open');
  window_?.setAttribute('aria-hidden',
    String(!window_?.classList.contains('chatbot--open')));
  if (window_?.classList.contains('chatbot--open')) input?.focus();
});
closeBtn?.addEventListener('click', () => {
  window_?.classList.remove('chatbot--open');
});

// масив для збереження історії
let chatHistory = JSON.parse(sessionStorage.getItem('chatHistory') || '[]');

// відновлення історії при завантаженні сторінки
if (chatHistory.length > 0 && messages) {
  messages.innerHTML = ''; // очищаємо дефолтне привітання
  chatHistory.forEach(msg => {
    if (msg.type === 'suggestion') {
      appendOrderSuggestion(msg.items, false);
    } else {
      appendMsg(msg.text, msg.type, false);
    }
  });
}

// функція відправки повідомлення на сервер
async function sendMessage() {
  const text = input?.value.trim();
  if (!text) return;

  appendMsg(text, 'user');
  chatHistory.push({ type: 'user', text: text });
  sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  
  input.value = '';
  input.disabled = true;
  sendBtn.disabled = true;

  // Індикатор "друкує..."
  const typing = appendMsg('• • •', 'typing');

  try {
    const res = await fetch('/api/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory }),
    });
    const data = await res.json();
    typing.remove();

    if (data.reply) {
      appendMsg(data.reply, 'bot');
      chatHistory.push({ type: 'bot', text: data.reply });
      sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));

      // Якщо бот виявив замовлення — показуємо кнопку-підказку і оновлюємо бейдж
      if (data.order_items && data.order_items.length > 0) {
        appendOrderSuggestion(data.order_items);
        chatHistory.push({ type: 'suggestion', items: data.order_items });
        sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        if (data.cart_count !== undefined && typeof updateCartBadge === 'function') {
          updateCartBadge(data.cart_count);
        }
      }
    } else {
      appendMsg('Виникла помилка. Спробуйте ще раз.', 'bot');
    }
  } catch (e) {
    console.error(e);
    typing.remove();
    appendMsg('Немає зв\'язку з сервером.', 'bot');
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

// функція для додавання нового повідомлення у вікно чату
function appendMsg(text, type, scroll = true) {
  const div = document.createElement('div');
  div.className = `chat-msg chat-msg--${type}`;
  div.textContent = text;
  messages?.appendChild(div);
  if (scroll) messages.scrollTop = messages.scrollHeight;
  return div;
}

// функція для показу підказки, якщо бот знайшов замовлення
function appendOrderSuggestion(items, scroll = true) {
  const wrap = document.createElement('div');
  wrap.className = 'chat-msg chat-msg--bot';
  wrap.innerHTML = `
    <strong>Успішно додано до кошика:</strong><br>
    ${items.map(i => `• ${i}`).join('<br>')}
    <br><a href="/cart" style="color:var(--color-accent);font-weight:600;display:inline-block;margin-top:5px;">
      Перейти до кошика →
    </a>`;
  messages?.appendChild(wrap);
  if (scroll) messages.scrollTop = messages.scrollHeight;
}

// обробники натискань на клавіатурі та кнопці відправки
sendBtn?.addEventListener('click', sendMessage);
input?.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

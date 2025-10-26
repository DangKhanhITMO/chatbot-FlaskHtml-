let flag_language = 'en';
let languageSelected = false;
let isBotTyping = false;
const historyKey = "chat_history";

// === SỬ DỤNG sessionStorage để reset khi reload ===
window.onload = () => {
  sessionStorage.removeItem(historyKey); // Xóa lịch sử mỗi khi load lại
  showWelcomeMessage();
  disableInput();
};

// Gửi tin nhắn khi nhấn Enter
document.addEventListener('keydown', function (e) {
  if (e.key === 'Enter') {
    const input = document.getElementById('user-input');
    if (!input.disabled && input.value.trim() !== '') {
      sendMessage();
    }
  }
});

function sendMessage() {
  const input = document.getElementById('user-input');
  const message = input.value.trim();

  if (!languageSelected || message === '') return;

  appendMessage('user', message);
  input.value = '';
  disableInput();
  showTypingIndicator();

  fetch('/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      question: message,
      flag_language: flag_language
    })
  })
  .then(res => res.json())
  .then(data => {
    removeTypingIndicator();
    if (data.answer) {
      appendMessage('bot', data.answer);
    } else {
      appendMessage('bot', 'Xin lỗi, tôi không tìm thấy câu trả lời phù hợp.');
    }
    enableInput();
  })
  .catch(err => {
    console.error('Lỗi khi gửi câu hỏi:', err);
    removeTypingIndicator();
    appendMessage('bot', 'Có lỗi xảy ra khi gửi câu hỏi. Vui lòng thử lại.');
    enableInput();
  });
}

// Hiển thị lựa chọn ngôn ngữ
function showWelcomeMessage() {
  const chatBox = document.getElementById('chat-box');
  chatBox.innerHTML = ''; // Xóa mọi nội dung cũ

  const systemMessage = document.createElement('div');
  systemMessage.className = 'message bot';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = `
    Which language would you like me to assist you with?<br><br>
    <button onclick="selectLanguage('vi')" class="lang-btn">Vietnamese</button>
    <button onclick="selectLanguage('ja')" class="lang-btn">Japanese</button>
    <button onclick="selectLanguage('en')" class="lang-btn">English (Default)</button>
  `;

  systemMessage.appendChild(bubble);
  chatBox.appendChild(systemMessage);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function selectLanguage(lang) {
  flag_language = lang;
  languageSelected = true;
  disableLanguageButtons();

  fetch('/init', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      flag_language: flag_language,
      message: 'hello'
    })
  })
  .then(res => res.json())
  .then(data => {
    appendMessage('bot', data.response);
    enableInput();
  })
  .catch(err => {
    console.error('Init error:', err);
    appendMessage('bot', 'Có lỗi xảy ra khi khởi tạo.');
  });
}

function disableInput() {
  const input = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  if (input) input.disabled = true;
  if (sendBtn) sendBtn.disabled = true;
}

function enableInput() {
  const input = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  if (input) input.disabled = false;
  if (sendBtn) sendBtn.disabled = false;
  input.focus();
}
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false   // ✅ 24h format
  });
}
function appendMessage(sender, text) {
  const chatBox = document.getElementById('chat-box');

  const messageDiv = document.createElement('div');
  messageDiv.className = 'message ' + sender;

  // Tạo avatar
  const avatar = document.createElement('img');
  avatar.className = 'avatar';
  avatar.src = sender === 'user'
    ? 'static/img/img3.png'
    : 'static/img/logo.jpg';
  avatar.alt = sender + ' avatar';

  // Tạo phần nội dung
  const contentWrapper = document.createElement('div');
  contentWrapper.className = 'content-wrapper';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const timestamp = document.createElement('div');
  timestamp.className = 'timestamp';
  timestamp.textContent = getCurrentTime();


  // Gắn vào tin nhắn theo hướng trái/phải
  if (sender === 'user') {
    messageDiv.appendChild(contentWrapper);
    messageDiv.appendChild(avatar);
  } else {
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentWrapper);
  }

  bubble.appendChild(timestamp); // timestamp nằm trong bubble
  contentWrapper.appendChild(bubble);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  saveMessageToHistory(sender, text);
}
// Spinner
function showTypingIndicator() {
  isBotTyping = true;
  const chatBox = document.getElementById('chat-box');
  const typing = document.createElement('div');
  typing.className = 'message bot typing-indicator';
  typing.innerHTML = `
    <div class="bubble">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  `;
  chatBox.appendChild(typing);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
  isBotTyping = false;
  const typing = document.querySelector('.typing-indicator');
  if (typing) typing.remove();
}

function disableLanguageButtons() {
  const buttons = document.querySelectorAll('.lang-btn');
  buttons.forEach(btn => {
    btn.disabled = true;
    btn.style.opacity = 0.5;
    btn.style.cursor = 'not-allowed';
  });
}

// === Lưu lịch sử vào sessionStorage thay vì localStorage ===
function saveMessageToHistory(sender, text) {
  let history = JSON.parse(sessionStorage.getItem(historyKey)) || [];
  history.push({ sender, text });
  sessionStorage.setItem(historyKey, JSON.stringify(history));
}

function loadChatHistory() {
  const history = JSON.parse(sessionStorage.getItem(historyKey)) || [];
  if (history.length > 0) {
    languageSelected = true;
    history.forEach(msg => appendMessage(msg.sender, msg.text));
    enableInput();
  }
}
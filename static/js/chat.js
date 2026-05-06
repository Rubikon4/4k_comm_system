let lastMessageId = typeof LAST_MESSAGE_ID !== 'undefined' ? LAST_MESSAGE_ID : 0;
let pollingTimer = null;

function getCsrfToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split('; csrftoken=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
}

function nl2br(str) {
    return escapeHtml(str).replace(/\n/g, '<br>');
}

function removeEmptyPlaceholder() {
    const placeholder = document.getElementById('empty-placeholder');
    if (placeholder) placeholder.remove();
}

function appendMessage(msg) {
    removeEmptyPlaceholder();
    const container = document.getElementById('messages-container');
    const isOwn = msg.author === CURRENT_USER;

    const wrapper = document.createElement('div');
    wrapper.id = `msg-${msg.id}`;
    wrapper.className = `message d-flex mb-2 ${isOwn ? 'message-mine justify-content-end' : 'message-other'}`;

    const authorRow = isOwn
        ? ''
        : `<div class="fw-bold small text-primary">${escapeHtml(msg.author)}</div>`;

    const body = msg.is_deleted
        ? '<em class="text-muted">Сообщение удалено</em>'
        : `<div>${nl2br(msg.text)}</div>`;

    wrapper.innerHTML = `
        <div class="message-bubble rounded p-2 px-3">
            ${authorRow}
            ${body}
            <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(msg.created_at)}</div>
        </div>`;

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}

function pollMessages() {
    if (document.hidden) return;
    fetch(`${POLLING_URL}?since=${lastMessageId}`, {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
    })
        .then(r => r.json())
        .then(data => {
            if (!data.messages) return;
            data.messages.forEach(msg => {
                if (!document.getElementById(`msg-${msg.id}`)) {
                    appendMessage(msg);
                }
                if (msg.id > lastMessageId) lastMessageId = msg.id;
            });
        })
        .catch(() => {});
}

function startPolling() {
    if (pollingTimer) return;
    pollingTimer = setInterval(pollMessages, 5000);
}

function stopPolling() {
    clearInterval(pollingTimer);
    pollingTimer = null;
}

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        pollMessages();
        startPolling();
    }
});

// Отправка сообщения
const messageForm = document.getElementById('message-form');
if (messageForm) {
    messageForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const textarea = document.getElementById('id_text');
        const text = textarea ? textarea.value.trim() : '';
        if (!text) return;

        fetch(SEND_URL, {
            method: 'POST',
            headers: {'X-CSRFToken': getCsrfToken()},
            body: new FormData(messageForm),
        })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    if (textarea) textarea.value = '';
                    if (data.message && !document.getElementById(`msg-${data.message.id}`)) {
                        appendMessage(data.message);
                        lastMessageId = Math.max(lastMessageId, data.message.id);
                    }
                } else {
                    alert(data.error || 'Ошибка при отправке сообщения.');
                }
            })
            .catch(() => alert('Ошибка сети. Попробуйте ещё раз.'));
    });

    // Отправка по Ctrl+Enter
    const textarea = document.getElementById('id_text');
    if (textarea) {
        textarea.addEventListener('keydown', function (e) {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                messageForm.dispatchEvent(new Event('submit', {bubbles: true}));
            }
        });
    }
}

// Скролл к последнему сообщению и запуск polling при загрузке
const container = document.getElementById('messages-container');
if (container) {
    container.scrollTop = container.scrollHeight;
}
startPolling();

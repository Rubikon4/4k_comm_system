function getCsrfToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split('; csrftoken=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function openWgModal(url) {
    loadIntoModal(url);
}

function loadIntoModal(url) {
    fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
        .then(r => r.text())
        .then(html => {
            document.getElementById('wg-modal-body').innerHTML = html;
            const el = document.getElementById('wg-modal');
            bootstrap.Modal.getOrCreateInstance(el).show();
            bindModalForms();
        });
}

function bindModalForms() {
    const form = document.querySelector('#wg-modal-body form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitModalForm(form);
    });
}

function submitModalForm(form) {
    fetch(form.action, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
        body: new FormData(form),
    })
    .then(response => {
        const ct = response.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) {
            return response.json().then(data => ({type: 'json', data}));
        }
        return response.text().then(html => ({type: 'html', html}));
    })
    .then(result => {
        if (result.type === 'json') {
            if (result.data.ok) {
                window.location.reload();
            } else {
                showModalError(result.data.error || 'Произошла ошибка');
            }
        } else {
            // Форма вернула HTML — валидационные ошибки: обновляем содержимое модала
            document.getElementById('wg-modal-body').innerHTML = result.html;
            bindModalForms();
        }
    });
}

function showModalError(message) {
    let el = document.getElementById('wg-modal-error');
    if (!el) {
        el = document.createElement('div');
        el.id = 'wg-modal-error';
        el.className = 'alert alert-danger mx-3 mt-2';
        const footer = document.querySelector('#wg-modal-body .modal-footer');
        if (footer) footer.before(el);
        else document.getElementById('wg-modal-body').appendChild(el);
    }
    el.textContent = message;
}

function uploadWgAttachment(formEl, uploadUrl, reloadUrl) {
    const fileInput = formEl.querySelector('input[type="file"]');
    if (!fileInput || !fileInput.files.length) {
        alert('Выберите файл для загрузки.');
        return;
    }
    fetch(uploadUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
        body: new FormData(formEl),
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            loadIntoModal(reloadUrl);
        } else {
            alert(data.error || 'Ошибка загрузки файла.');
        }
    })
    .catch(() => alert('Ошибка сети.'));
}

function deleteWgAttachment(deleteUrl, reloadUrl, name) {
    if (!confirm(`Удалить файл «${name}»?`)) return;
    fetch(deleteUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            loadIntoModal(reloadUrl);
        } else {
            alert(data.error || 'Ошибка удаления файла.');
        }
    })
    .catch(() => alert('Ошибка сети.'));
}

function deactivateGroup(url, name) {
    if (!confirm(`Деактивировать группу «${name}» и все её подгруппы? Это действие необратимо.`)) return;
    fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            window.location.reload();
        } else {
            alert(data.error || 'Ошибка деактивации');
        }
    });
}

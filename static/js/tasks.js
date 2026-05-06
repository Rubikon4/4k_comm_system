function getCsrfToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split('; csrftoken=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function openTaskModal(url) {
    loadIntoTaskModal(url);
}

function loadIntoTaskModal(url) {
    fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
        .then(r => r.text())
        .then(html => {
            document.getElementById('task-modal-body').innerHTML = html;
            const el = document.getElementById('task-modal');
            bootstrap.Modal.getOrCreateInstance(el).show();
            bindTaskForms();
        });
}

function bindTaskForms() {
    const form = document.querySelector('#task-modal-body form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitTaskForm(form);
    });
}

function submitTaskForm(form) {
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
                showTaskError(result.data.error || 'Произошла ошибка');
            }
        } else {
            document.getElementById('task-modal-body').innerHTML = result.html;
            bindTaskForms();
        }
    });
}

function showTaskError(message) {
    let el = document.getElementById('task-modal-error');
    if (!el) {
        el = document.createElement('div');
        el.id = 'task-modal-error';
        el.className = 'alert alert-danger mx-3 mt-2';
        const footer = document.querySelector('#task-modal-body .modal-footer');
        if (footer) footer.before(el);
        else document.getElementById('task-modal-body').appendChild(el);
    }
    el.textContent = message;
}

function postTaskAction(url, confirmMsg) {
    if (confirmMsg && !confirm(confirmMsg)) return;
    fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            window.location.reload();
        } else {
            alert(data.error || 'Ошибка');
        }
    });
}

function uploadTaskAttachment(formEl, uploadUrl, reloadUrl) {
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
            loadIntoTaskModal(reloadUrl);
        } else {
            alert(data.error || 'Ошибка загрузки файла.');
        }
    })
    .catch(() => alert('Ошибка сети.'));
}

function deleteTaskAttachment(deleteUrl, reloadUrl, name) {
    if (!confirm(`Удалить файл «${name}»?`)) return;
    fetch(deleteUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            loadIntoTaskModal(reloadUrl);
        } else {
            alert(data.error || 'Ошибка удаления файла.');
        }
    })
    .catch(() => alert('Ошибка сети.'));
}

// Скрывает/показывает поле recurrence_days в зависимости от is_recurring
document.addEventListener('DOMContentLoaded', function () {
    const recurringCheckbox = document.getElementById('id_is_recurring');
    const recurrenceRow = document.getElementById('recurrence-days-row');
    if (!recurringCheckbox || !recurrenceRow) return;

    function toggle() {
        recurrenceRow.style.display = recurringCheckbox.checked ? '' : 'none';
    }
    toggle();
    recurringCheckbox.addEventListener('change', toggle);
});

// Состояние флага (true - ассистент активен)
let isAssistantActive = true;

// Ждем загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('Скрипт загружен');

    // Находим кнопку
    const stopButton = document.querySelector('.stop-btn');

    if (stopButton) {
        stopButton.addEventListener('click', toggleAssistant);
    }
});

// Функция переключения ассистента
async function toggleAssistant() {
    try {
        // Меняем визуальное состояние сразу для отзывчивости
        isAssistantActive = !isAssistantActive;
        updateUI();

        // Проверяем, доступен ли pywebview API
        if (window.pywebview && window.pywebview.api) {
            // Вызываем Python метод
            const result = await window.pywebview.api.toggle_assistant(isAssistantActive);
            console.log('Ответ от Python:', result);

            // Синхронизируем состояние с Python (на случай если Python изменил флаг)
            if (result !== undefined) {
                isAssistantActive = result;
                updateUI();
            }
        } else {
            console.log('pywebview не доступен (работа в обычном браузере)');
            // Просто эмулируем для тестирования в браузере
            console.log(`Флаг изменен на: ${isAssistantActive}`);
        }

    } catch (error) {
        console.error('Ошибка при вызове Python:', error);
    }
}

// Обновление UI в зависимости от флага
function updateUI() {
    const stopButton = document.querySelector('.stop-btn');
    const statusElement = document.querySelector('.status-active');
    const micCircle = document.querySelector('.mic-core');

    if (isAssistantActive) {
        // Ассистент активен
        if (stopButton) {
            stopButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="6" y="4" width="4" height="16" rx="1"/>
                    <rect x="14" y="4" width="4" height="16" rx="1"/>
                </svg>
                Остановить ассистента
            `;
            stopButton.style.background = "rgba(239, 68, 68, 0.2)";
            stopButton.style.borderColor = "#ef4444";
        }
        if (statusElement) statusElement.textContent = "Активен";
        if (statusElement) statusElement.style.color = "#22c55e";
        if (micCircle) micCircle.style.background = "radial-gradient(circle, rgba(34,197,94,0.25), rgba(34,197,94,0.05) 60%, transparent)";

    } else {
        // Ассистент остановлен
        if (stopButton) {
            stopButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 8v4M12 16h.01"/>
                </svg>
                Запустить ассистента
            `;
            stopButton.style.background = "rgba(34, 197, 94, 0.2)";
            stopButton.style.borderColor = "#22c55e";
        }
        if (statusElement) statusElement.textContent = "Остановлен";
        if (statusElement) statusElement.style.color = "#ef4444";
        if (micCircle) micCircle.style.background = "radial-gradient(circle, rgba(239,68,68,0.25), rgba(239,68,68,0.05) 60%, transparent)";
    }

    // Меняем класс для дополнительных стилей
    if (stopButton) {
        if (isAssistantActive) {
            stopButton.classList.remove('inactive');
            stopButton.classList.add('active');
        } else {
            stopButton.classList.remove('active');
            stopButton.classList.add('inactive');
        }
    }
}

// Дополнительная функция для ручного вызова из Python
function setAssistantState(state) {
    isAssistantActive = state;
    updateUI();
    console.log(`Состояние изменено Python на: ${state}`);
}

// Экспортируем функции в глобальный объект для доступа из Python
window.assistantUI = {
    setState: setAssistantState,
    getState: () => isAssistantActive
};
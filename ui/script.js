// script.js - полная версия для EmilyOS Assistant

function setupCoreEventListeners() {
    // Событие изменения состояния
    window.addEventListener('state_change', (event) => {
        if (event.detail && event.detail.state) {
            console.log('Состояние изменилось:', event.detail.state);
            updateMicrophoneAnimation(event.detail.state, true);

            // Обновляем текст статуса
            const statusSub = document.querySelector('.status-sub');
            if (statusSub) {
                statusSub.textContent = getStateText(event.detail.state);
            }
        }
    });

    // Событие пробуждения
    window.addEventListener('wake_word', (event) => {
        console.log('Пробуждение!', event.detail);
        // Можно добавить визуальный эффект при пробуждении
        const micCore = document.querySelector('.mic-core');
        if (micCore) {
            micCore.style.transform = 'scale(1.1)';
            setTimeout(() => {
                micCore.style.transform = 'scale(1)';
            }, 200);
        }
    });

    // Событие остановки ассистента
    window.addEventListener('assistant_stopped', () => {
        updateMicrophoneAnimation('idle', false);
    });
}

console.log('=== ДИАГНОСТИКА API ===');
console.log('1. window.pywebview:', window.pywebview);
console.log('2. window.external:', window.external);
console.log('3. chrome.webview:', window.chrome?.webview);

// Универсальная функция получения API
function getApi() {
    if (window.pywebview && window.pywebview.api) {
        return window.pywebview.api;
    }
    if (window.external && typeof window.external.getApi === 'function') {
        return window.external;
    }
    if (window.chrome && window.chrome.webview && window.chrome.webview.hostObjects) {
        return window.chrome.webview.hostObjects.sync;
    }
    return null;
}

// Глобальная переменная для API
let api = null;
let refreshInterval = null;

// ========== ИНИЦИАЛИЗАЦИЯ ==========
document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 DOM загружен');

    let attempts = 0;
    const maxAttempts = 20;

    const tryGetApi = setInterval(() => {
        attempts++;
        const foundApi = getApi();
        if (foundApi) {
            api = foundApi;
            console.log('✅ API найден!');
            clearInterval(tryGetApi);
            loadAllData();
            startAutoRefresh();
            refreshCommandsTab();
        } else if (attempts >= maxAttempts) {
            console.error('❌ API не найден после', maxAttempts, 'попыток');
            clearInterval(tryGetApi);
            showMockData();
        }
    }, 500);

    setupCoreEventListeners();
    setupEventListeners();
    setupTabs();
});

// ========== АВТООБНОВЛЕНИЕ ==========
function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(async () => {
        if (api && document.querySelector('.tab.active')?.id === 'homeTab') {
            try {
                await loadAllData();
                console.log('🔄 Данные обновлены');
            } catch(e) {
                console.error('Ошибка автообновления:', e);
            }
        }
    }, 3000);
}

// ========== ЗАГРУЗКА ДАННЫХ ГЛАВНОЙ ВКЛАДКИ ==========
async function loadAllData() {
    if (!api) {
        console.error('API не доступен');
        return;
    }

    try {
        console.log('🔄 Загрузка данных...');

        const status = await api.get_status();
        console.log('Статус:', status);
        updateStatusDisplay(status);

        const todayStats = await api.get_today_stats();
        console.log('Статистика за сегодня:', todayStats);
        updateTodayStats(todayStats);

        const uptime = await api.get_uptime();
        console.log('Время работы:', uptime);
        updateUptime(uptime);

        const lastCommand = await api.get_last_command();
        console.log('Последняя команда:', lastCommand);
        updateLastCommand(lastCommand);

        const pipelineStatus = await api.get_pipeline_status();
        console.log('Pipeline:', pipelineStatus);
        updatePipelineStatus(pipelineStatus);

        const recentCommands = await api.get_recent_commands();
        console.log('Недавние команды:', recentCommands);
        updateRecentCommands(recentCommands);

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// ========== ОБНОВЛЕНИЕ UI ГЛАВНОЙ ВКЛАДКИ ==========
function updateStatusDisplay(status) {
    let statusElement = document.querySelector('.status-active');
    if (!statusElement) {
        const statCards = document.querySelectorAll('.stat-card');
        for (let card of statCards) {
            const label = card.querySelector('.stat-label');
            if (label && label.textContent === 'Статус ассистента') {
                statusElement = card.querySelector('.stat-value');
                break;
            }
        }
    }

    if (statusElement) {
        if (status.is_active) {
            statusElement.innerHTML = '● Активен';
            statusElement.style.color = '#22c55e';
        } else {
            statusElement.innerHTML = '● Остановлен';
            statusElement.style.color = '#ef4444';
        }
    }

    const statusSub = document.querySelector('.status-sub');
    if (statusSub && api) {
        api.get_state_text().then(text => {
            statusSub.textContent = text;
        }).catch(() => {
            statusSub.textContent = getStateText(status.state);
        });
    }
}

function getStateText(state) {
    const states = {
        'idle': 'Ожидание активации...',
        'listening': '🎤 Слушаю команду...',
        'processing': '🔄 Обработка...'
    };
    return states[state] || 'Готов к работе';
}

function updateTodayStats(stats) {
    const statCards = document.querySelectorAll('.stat-card');
    for (let card of statCards) {
        const label = card.querySelector('.stat-label');
        if (label && label.textContent === 'Выполнено сегодня') {
            const valueEl = card.querySelector('.stat-value');
            if (valueEl) {
                valueEl.innerHTML = `${stats.total} <span class="stat-small">команд</span>`;
            }
            const noteEl = card.querySelector('.stat-note.success');
            if (noteEl) {
                noteEl.textContent = `Успешно: ${stats.successful} (${stats.success_rate}%)`;
            }
            break;
        }
    }
}

function updateUptime(uptime) {
    const statCards = document.querySelectorAll('.stat-card');
    for (let card of statCards) {
        const label = card.querySelector('.stat-label');
        if (label && label.textContent === 'Время работы') {
            const valueEl = card.querySelector('.stat-value');
            if (valueEl) {
                valueEl.textContent = uptime;
            }
            break;
        }
    }
}

function updateLastCommand(lastCommand) {
    const commandText = document.querySelector('.last-command-text');
    const commandTime = document.querySelector('.last-command-time');

    if (commandText && lastCommand && lastCommand.command) {
        commandText.textContent = `«${lastCommand.command.substring(0, 50)}»`;
    } else if (commandText) {
        commandText.textContent = '«—»';
    }

    if (commandTime && lastCommand && lastCommand.timestamp) {
        const time = new Date(lastCommand.timestamp).toLocaleTimeString();
        commandTime.textContent = `${time} → выполнено`;
    } else if (commandTime) {
        commandTime.textContent = 'Нет выполненных команд';
    }
}

function updatePipelineStatus(status) {
    const steps = document.querySelectorAll('.pipeline-step');
    if (steps.length >= 4) {
        const step1Status = steps[0]?.querySelector('.step-status');
        if (step1Status) step1Status.textContent = status.wake_word_status || 'Слушает...';

        const step2Module = steps[1]?.querySelector('.step-module');
        const step2Status = steps[1]?.querySelector('.step-status');
        if (step2Module) step2Module.textContent = status.stt || 'Vosk STT';
        if (step2Status) step2Status.textContent = status.stt_status || 'Готов';

        const step3Module = steps[2]?.querySelector('.step-module');
        const step3Status = steps[2]?.querySelector('.step-status');
        if (step3Module) step3Module.textContent = status.nlu || 'RuleBased NLU';
        if (step3Status) step3Status.textContent = status.nlu_status || 'Готов';

        const step4Module = steps[3]?.querySelector('.step-module');
        const step4Status = steps[3]?.querySelector('.step-status');
        if (step4Module) step4Module.textContent = status.executor || 'Command Executor';
        if (step4Status) step4Status.textContent = status.executor_status || 'Готов';
    }
}

function updateRecentCommands(commands) {
    const recentList = document.querySelector('.recent-list');
    if (!recentList) return;

    if (!commands || commands.length === 0) {
        recentList.innerHTML = '<div class="recent-item"><span class="recent-name">Нет команд</span></div>';
        return;
    }

    recentList.innerHTML = commands.map(cmd => `
        <div class="recent-item">
            <span class="recent-icon">🎤</span>
            <span class="recent-name">${escapeHtml(cmd.name.substring(0, 40))}</span>
            <span class="recent-count">${cmd.count} раз</span>
        </div>
    `).join('');
}

// ========== ВКЛАДКА ЖУРНАЛ ==========
async function refreshLogsTab() {
    if (!api) return;

    try {
        const history = await api.get_history(100);
        updateLogsList(history);
        updateLogsStats();
    } catch (error) {
        console.error('Ошибка загрузки логов:', error);
    }
}

function updateLogsList(historyData) {
    const logsContainer = document.querySelector('.logs-container');
    if (!logsContainer) return;

    if (!historyData || historyData.length === 0) {
        logsContainer.innerHTML = '<div class="log-item"><div class="log-content"><div class="log-message">Нет записей в истории</div></div></div>';
        return;
    }

    logsContainer.innerHTML = historyData.slice().reverse().map(entry => {
        const time = new Date(entry.timestamp).toLocaleTimeString();
        const isError = entry.response?.toLowerCase().includes('не понял') || entry.response?.toLowerCase().includes('не удалось');
        const badgeClass = isError ? 'error' : 'success';
        const badgeText = isError ? 'ERR' : 'OK';

        return `
            <div class="log-item ${isError ? 'error' : 'success'}">
                <div class="log-badge ${badgeClass}">${badgeText}</div>
                <div class="log-content">
                    <div class="log-message">
                        Команда: "${escapeHtml(entry.command)}" → ${escapeHtml(entry.response)}
                    </div>
                    <div class="log-meta">
                        Интент: ${entry.intent} • ${time}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function updateLogsStats() {
    if (!api) return;

    try {
        const stats = await api.get_stats();
        const todayStats = await api.get_today_stats();

        const eventCountEl = document.querySelector('.log-stat-value');
        const errorCountEl = document.querySelector('.log-stat-value.red');
        const successRateEl = document.querySelector('.log-stat-value.green');
        const lastActivityEl = document.querySelector('.log-stat-text');

        if (eventCountEl) eventCountEl.textContent = stats.total_commands || 0;
        if (errorCountEl) errorCountEl.textContent = todayStats.failed || 0;
        if (successRateEl) successRateEl.textContent = `${todayStats.success_rate || 0}%`;
        if (lastActivityEl && stats.total_commands > 0) lastActivityEl.textContent = 'только что';
    } catch (error) {
        console.error('Ошибка обновления статистики логов:', error);
    }
}

// ========== ВКЛАДКА КОМАНДЫ ==========
async function refreshCommandsTab() {
    if (!api) {
        console.error('API не доступен');
        showMockCommands();
        return;
    }

    try {
        const capabilities = await api.get_capabilities();
        console.log('Загружены команды, количество:', capabilities.intents?.length || 0);
        updateCommandsGrid(capabilities);
    } catch (error) {
        console.error('Ошибка загрузки команд:', error);
        showMockCommands();
    }
}

function updateCommandsGrid(capabilities) {
    const commandsGrid = document.querySelector('.commands-grid');
    if (!commandsGrid) return;

    const intents = capabilities.intents || [];
    const totalCommands = capabilities.commands_count || intents.length;

    const commandsTitle = document.querySelector('.commands-title');
    if (commandsTitle) {
        commandsTitle.innerHTML = `Голосовые команды <span style="font-size: 18px; color: #a78bfa;">(${totalCommands})</span>`;
    }

    if (intents.length === 0) {
        commandsGrid.innerHTML = `
            <div class="command-card" style="grid-column: span 3; text-align: center;">
                <div class="command-name">Нет доступных команд</div>
                <div class="command-description">Добавьте команды через NLU модуль</div>
            </div>
        `;
        return;
    }

    const displayedIntents = intents.slice(0, 12);

    commandsGrid.innerHTML = displayedIntents.map(intent => `
        <div class="command-card">
            <div class="command-top">
                <div class="command-icon ${getIntentColor(intent)}">
                    ${getIntentEmoji(intent)}
                </div>
                <div class="command-status active">ACTIVE</div>
            </div>
            <div class="command-name">${formatIntentName(intent)}</div>
            <div class="command-trigger">
                Триггер: «${getExamplePhrase(intent)}»
            </div>
            <div class="command-description">
                ${getIntentDescription(intent)}
            </div>
            <div class="command-tags">
                <span>${getIntentCategory(intent)}</span>
                <span>голосовая</span>
            </div>
            <div class="command-actions">
                <button class="cmd-btn run" data-intent="${intent}">▶ Выполнить</button>
                <button class="cmd-btn edit" data-intent="${intent}">✏️ Редактировать</button>
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.cmd-btn.run').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const intent = btn.dataset.intent;
            if (api) {
                showNotification(`🎤 Выполняю: ${formatIntentName(intent)}`, 'info');
                try {
                    const result = await api.execute_command(intent);
                    showNotification(`✅ ${result.response}`, 'success');
                    setTimeout(() => {
                        if (document.querySelector('.tab.active')?.id === 'logsTab') refreshLogsTab();
                        if (document.querySelector('.tab.active')?.id === 'homeTab') loadAllData();
                    }, 500);
                } catch(e) {
                    showNotification(`❌ Ошибка: ${e.message}`, 'error');
                }
            }
        });
    });

    document.querySelectorAll('.cmd-btn.edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            showNotification(`✏️ Редактирование команды будет доступно в следующей версии`, 'info');
        });
    });

    setupCommandSearch();
}

function setupCommandSearch() {
    const searchInput = document.querySelector('.commands-search');
    const filterSelect = document.querySelector('.commands-filter');

    if (searchInput) {
        const newSearch = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearch, searchInput);
        newSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.command-card').forEach(card => {
                const name = card.querySelector('.command-name')?.textContent.toLowerCase() || '';
                const trigger = card.querySelector('.command-trigger')?.textContent.toLowerCase() || '';
                card.style.display = (name.includes(query) || trigger.includes(query)) ? 'block' : 'none';
            });
        });
    }

    if (filterSelect) {
        const newFilter = filterSelect.cloneNode(true);
        filterSelect.parentNode.replaceChild(newFilter, filterSelect);
        newFilter.addEventListener('change', (e) => {
            const category = e.target.value;
            document.querySelectorAll('.command-card').forEach(card => {
                if (category === 'Все категории') {
                    card.style.display = 'block';
                } else {
                    const tags = card.querySelectorAll('.command-tags span');
                    let found = false;
                    tags.forEach(tag => { if (tag.textContent === category) found = true; });
                    card.style.display = found ? 'block' : 'none';
                }
            });
        });
    }
}

// ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КОМАНД ==========
function getIntentEmoji(intent) {
    const emojis = {
        'open_app': '🚀', 'set_volume': '🔊', 'volume_up': '📢', 'volume_down': '🔉', 'mute': '🔇',
        'time': '⏰', 'date': '📅', 'google_search': '🔍', 'wikipedia_search': '📚',
        'screenshot': '📸', 'lock_pc': '🔒', 'shutdown': '⏻', 'restart': '🔄',
        'greeting': '👋', 'goodbye': '👋', 'weather': '🌤️', 'capabilities': '🤖',
        'how_are_you': '💬', 'thanks': '🙏', 'help': '❓', 'next_track': '⏭️',
        'prev_track': '⏮️', 'play_pause': '⏯️', 'create_reminder': '📌', 'write_note': '📝'
    };
    return emojis[intent] || '🎤';
}

function getIntentColor(intent) {
    const colors = { 'open_app': 'purple', 'set_volume': 'green', 'time': 'blue', 'google_search': 'purple', 'screenshot': 'red' };
    return colors[intent] || 'purple';
}

function getIntentCategory(intent) {
    if (intent.includes('volume') || intent === 'mute') return 'Системные';
    if (intent.includes('track') || intent === 'play_pause') return 'Медиа';
    if (intent.includes('search')) return 'Браузер';
    if (intent.includes('reminder') || intent.includes('note')) return 'Утилиты';
    if (intent === 'time' || intent === 'date' || intent === 'weather') return 'Информация';
    return 'Основные';
}

function getIntentDescription(intent) {
    const descriptions = {
        'open_app': 'Запускает указанное приложение',
        'set_volume': 'Устанавливает уровень громкости',
        'volume_up': 'Увеличивает громкость на 5%',
        'volume_down': 'Уменьшает громкость на 5%',
        'mute': 'Полностью отключает звук',
        'time': 'Сообщает текущее время',
        'date': 'Сообщает текущую дату',
        'google_search': 'Выполняет поиск в Google',
        'wikipedia_search': 'Ищет информацию в Википедии',
        'screenshot': 'Создаёт скриншот экрана',
        'lock_pc': 'Блокирует компьютер',
        'greeting': 'Приветствие ассистента',
        'weather': 'Показывает прогноз погоды',
        'capabilities': 'Список всех возможностей',
        'next_track': 'Следующий трек в медиаплеере',
        'prev_track': 'Предыдущий трек',
        'play_pause': 'Пауза/воспроизведение',
        'create_reminder': 'Создаёт напоминание',
        'write_note': 'Сохраняет заметку'
    };
    return descriptions[intent] || 'Голосовая команда для управления компьютером';
}

function formatIntentName(intent) {
    const names = {
        'open_app': 'Открыть приложение', 'set_volume': 'Установить громкость',
        'volume_up': 'Увеличить громкость', 'volume_down': 'Уменьшить громкость',
        'mute': 'Выключить звук', 'time': 'Текущее время', 'date': 'Текущая дата',
        'google_search': 'Поиск в Google', 'wikipedia_search': 'Поиск в Википедии',
        'open_url': 'Открыть сайт', 'close_app': 'Закрыть приложение',
        'screenshot': 'Сделать скриншот', 'lock_pc': 'Блокировать компьютер',
        'shutdown': 'Выключить компьютер', 'restart': 'Перезагрузить компьютер',
        'weather': 'Погода', 'greeting': 'Приветствие', 'goodbye': 'Прощание',
        'how_are_you': 'Как дела?', 'thanks': 'Спасибо', 'capabilities': 'Возможности',
        'help': 'Помощь', 'next_track': 'Следующий трек', 'prev_track': 'Предыдущий трек',
        'play_pause': 'Воспроизвести/Пауза', 'create_reminder': 'Создать напоминание',
        'write_note': 'Создать заметку'
    };
    return names[intent] || intent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getExamplePhrase(intent) {
    const examples = {
        'open_app': 'открой браузер', 'set_volume': 'установи громкость на 50',
        'time': 'который час', 'date': 'какая дата', 'screenshot': 'сделай скриншот',
        'lock_pc': 'заблокируй компьютер', 'weather': 'погода в Москве',
        'google_search': 'найди в гугле Python', 'create_reminder': 'напомни купить молоко'
    };
    return examples[intent] || intent;
}

// ========== МОК ДАННЫЕ ==========
function showMockData() {
    console.log('📊 Показываем тестовые данные');
    updateTodayStats({ total: 128, successful: 124, success_rate: 97 });
    updateUptime("03ч 42мин");
    updateLastCommand({ command: "открой браузер", timestamp: new Date().toISOString() });
    updatePipelineStatus({
        wake_word_status: "Слушает 'computer'", stt: "Vosk STT", stt_status: "Модель: ru-small",
        nlu: "RuleBased NLU", nlu_status: "Правил: 34",
        executor: "Command Executor", executor_status: "Доступно: 34 команд"
    });
    updateRecentCommands([{ name: "открой браузер", count: 12 }, { name: "который час", count: 8 }]);
}

function showMockCommands() {
    const commandsGrid = document.querySelector('.commands-grid');
    if (!commandsGrid) return;

    const mockIntents = ['open_app', 'set_volume', 'time', 'date', 'google_search', 'screenshot', 'lock_pc', 'greeting', 'weather', 'next_track'];
    commandsGrid.innerHTML = mockIntents.map(intent => `
        <div class="command-card">
            <div class="command-top">
                <div class="command-icon ${getIntentColor(intent)}">${getIntentEmoji(intent)}</div>
                <div class="command-status active">ACTIVE</div>
            </div>
            <div class="command-name">${formatIntentName(intent)}</div>
            <div class="command-trigger">Триггер: «${getExamplePhrase(intent)}»</div>
            <div class="command-description">${getIntentDescription(intent)}</div>
            <div class="command-actions"><button class="cmd-btn run" data-intent="${intent}">▶ Выполнить</button></div>
        </div>
    `).join('');
    document.querySelectorAll('.cmd-btn.run').forEach(btn => {
        btn.addEventListener('click', () => showNotification(`🎤 Демо-режим: команда "${btn.dataset.intent}"`, 'info'));
    });
}

// ========== УВЕДОМЛЕНИЯ ==========
function showNotification(message, type = 'info') {
    const colors = { success: '#22c55e', error: '#ef4444', warning: '#f59e0b', info: '#6366f1' };
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; background: ${colors[type] || colors.info};
        border: none; border-radius: 12px; padding: 12px 20px; color: white; z-index: 10000;
        animation: slideIn 0.3s ease; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => { notification.style.opacity = '0'; notification.style.transition = 'opacity 0.3s'; setTimeout(() => notification.remove(), 300); }, 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== ОБРАБОТЧИКИ СОБЫТИЙ ==========
function setupEventListeners() {
    const stopButton = document.querySelector('.stop-btn');
if (stopButton) {
    stopButton.addEventListener('click', async () => {
        if (api) {
            try {
                const newState = await api.toggle_listening();
                console.log('Новое состояние:', newState);

                // Мгновенное обновление UI
                const status = await api.get_status();
                updateStatusDisplay(status);
                updateMicrophoneAnimation(status.state, status.is_active);

                // Меняем текст кнопки
                if (newState) {
                    stopButton.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="6" y="4" width="4" height="16" rx="1"/>
                            <rect x="14" y="4" width="4" height="16" rx="1"/>
                        </svg>
                        Остановить ассистента
                    `;
                    stopButton.style.background = "rgba(239, 68, 68, 0.2)";
                    stopButton.style.borderColor = "#ef4444";
                } else {
                    stopButton.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 8v4M12 16h.01"/>
                        </svg>
                        Запустить ассистента
                    `;
                    stopButton.style.background = "rgba(34, 197, 94, 0.2)";
                    stopButton.style.borderColor = "#22c55e";
                }
            } catch(e) {
                console.error('Ошибка:', e);
            }
        }
    });
}

    const pipelineBtn = document.getElementById('openPipelineSettings');
    if (pipelineBtn) {
        pipelineBtn.addEventListener('click', () => {
            document.querySelector('[data-tab="modulesTab"]')?.click();
        });
    }

    const teachBtn = document.getElementById('teachCommandBtn');
    if (teachBtn) {
        teachBtn.addEventListener('click', () => {
            const command = prompt('Введите текстовую команду:');
            if (command && api) {
                api.process_text_command(command);
                setTimeout(() => loadAllData(), 500);
            }
        });
    }

    const settingsBtn = document.getElementById('voiceTrainingBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            document.querySelector('[data-tab="settingsTab"]')?.click();
        });
    }

    const clearLogsBtn = document.querySelector('.logs-actions .action-btn:last-child');
    if (clearLogsBtn && api) {
        clearLogsBtn.addEventListener('click', async () => {
            if (confirm('Очистить всю историю команд?')) {
                await api.clear_history();
                await refreshLogsTab();
                showNotification('История очищена', 'success');
            }
        });
    }

    const searchInput = document.querySelector('.logs-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.log-item').forEach(item => {
                item.style.display = item.textContent.toLowerCase().includes(query) ? 'flex' : 'none';
            });
        });
    }

    const filterSelect = document.querySelector('.logs-select');
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            const filter = e.target.value;
            document.querySelectorAll('.log-item').forEach(item => {
                if (filter === 'Все события') {
                    item.style.display = 'flex';
                } else {
                    const badge = item.querySelector('.log-badge')?.textContent;
                    item.style.display = badge === filter ? 'flex' : 'none';
                }
            });
        });
    }

    const saveSettingsBtn = document.querySelector('.save-settings-btn');
    if (saveSettingsBtn && api) {
        saveSettingsBtn.addEventListener('click', async () => {
            const ttsToggle = document.querySelector('.settings-switch-row .switch input');
            const settings = { tts_enabled: ttsToggle?.checked || true };
            await api.save_settings(settings);
            showNotification('Настройки сохранены', 'success');
        });
    }
}

// Добавляем CSS анимацию для уведомлений
const style = document.createElement('style');
style.textContent = `@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`;
document.head.appendChild(style);

// ========== ВКЛАДКА МОДУЛИ ==========
let draggedModule = null;

async function refreshModulesTab() {
    if (!api) {
        console.error('API не доступен');
        showMockModules();
        return;
    }

    try {
        // Загружаем доступные модули
        const availableModules = await api.get_available_modules();
        console.log('Доступные модули:', availableModules);
        updateModulesLibrary(availableModules);

        // Загружаем текущий pipeline
        const currentPipeline = await api.get_current_pipeline();
        console.log('Текущий pipeline:', currentPipeline);
        updatePipelineSlots(currentPipeline);

        // Настраиваем drag & drop
        setupDragAndDrop();

    } catch (error) {
        console.error('Ошибка загрузки модулей:', error);
        showMockModules();
    }
}

function updateModulesLibrary(modules) {
    const libraryContainer = document.querySelector('.modules-library');
    if (!libraryContainer) {
        console.error('modules-library не найден');
        return;
    }

    const panelTitle = libraryContainer.querySelector('.panel-title');
    libraryContainer.innerHTML = '';
    if (panelTitle) libraryContainer.appendChild(panelTitle);

    if (!modules || modules.length === 0) {
        const emptyMsg = document.createElement('div');
        emptyMsg.style.cssText = 'padding: 20px; text-align: center; color: #94a3b8;';
        emptyMsg.textContent = 'Нет доступных модулей';
        libraryContainer.appendChild(emptyMsg);
        return;
    }

    // Фильтруем дубликаты по id
    const uniqueModules = [];
    const seenIds = new Set();
    for (const module of modules) {
        if (!seenIds.has(module.id)) {
            seenIds.add(module.id);
            uniqueModules.push(module);
        }
    }

    const grouped = {
        activation: uniqueModules.filter(m => m.type === 'activation'),
        stt: uniqueModules.filter(m => m.type === 'stt'),
        nlp: uniqueModules.filter(m => m.type === 'nlp'),
        tts: uniqueModules.filter(m => m.type === 'tts')
    };

    const typeNames = {
        activation: '🔊 Активация (Wake Word)',
        stt: '🎤 Распознавание речи (STT)',
        nlp: '🧠 Анализ команд (NLU)',
        tts: '🔊 Синтез речи (TTS)'
    };

    for (const [type, mods] of Object.entries(grouped)) {
        if (mods.length > 0) {
            const typeHeader = document.createElement('div');
            typeHeader.style.cssText = 'margin: 16px 0 8px 0; font-size: 12px; color: #a78bfa; font-weight: 600; padding-left: 8px;';
            typeHeader.textContent = typeNames[type] || type.toUpperCase();
            libraryContainer.appendChild(typeHeader);

            mods.forEach(module => {
                const moduleCard = document.createElement('div');
                moduleCard.className = 'module-card';
                moduleCard.setAttribute('draggable', 'true');
                moduleCard.setAttribute('data-type', module.type);
                moduleCard.setAttribute('data-id', module.id);
                moduleCard.setAttribute('data-name', module.name);

                let iconColor = 'purple';
                if (module.type === 'stt') iconColor = 'green';
                if (module.type === 'tts') iconColor = 'blue';
                if (module.type === 'nlp') iconColor = 'red';

                moduleCard.innerHTML = `
                    <div class="module-icon ${iconColor}">
                        ${module.icon || '🔧'}
                    </div>
                    <div class="module-info">
                        <div class="module-name">${escapeHtml(module.name)}</div>
                        <div class="module-desc">${escapeHtml(module.description || 'Модуль обработки')}</div>
                    </div>
                    <div class="module-type">${module.type.toUpperCase()}</div>
                `;

                libraryContainer.appendChild(moduleCard);
            });
        }
    }

    setupDragAndDrop();
}

function updatePipelineSlots(pipeline) {
    const slots = document.querySelectorAll('.pipeline-slot');

    slots.forEach(slot => {
        const acceptType = slot.dataset.accept;
        const slotLabel = slot.querySelector('.slot-label');
        const slotContent = slot.querySelector('.slot-content');

        if (!slotContent) return;

        // Находим модуль для этого слота
        let moduleData = null;
        if (acceptType === 'activation' && pipeline.activation) moduleData = pipeline.activation;
        if (acceptType === 'stt' && pipeline.stt) moduleData = pipeline.stt;
        if (acceptType === 'nlp' && pipeline.nlp) moduleData = pipeline.nlp;
        if (acceptType === 'tts' && pipeline.tts) moduleData = pipeline.tts;

        if (moduleData) {
            let iconColor = 'purple';
            if (moduleData.type === 'stt') iconColor = 'green';
            if (moduleData.type === 'tts') iconColor = 'blue';
            if (moduleData.type === 'nlp') iconColor = 'red';

            slotContent.innerHTML = `
                <div class="module-card" style="cursor: default; background: rgba(124,58,237,0.1); margin: 0;" data-id="${moduleData.id}">
                    <div class="module-icon ${iconColor}" style="width: 40px; height: 40px;">
                        ${moduleData.icon}
                    </div>
                    <div class="module-info">
                        <div class="module-name">${escapeHtml(moduleData.name)}</div>
                        <div class="module-desc">${escapeHtml(moduleData.description || 'Активен')}</div>
                    </div>
                    <div class="module-type" style="background: rgba(34,197,94,0.15); color: #22c55e;">АКТИВЕН</div>
                </div>
            `;
        } else {
            slotContent.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #94a3b8;">
                    Перетащите модуль сюда
                </div>
            `;
        }
    });
}

function setupDragAndDrop() {
    // Находим все draggable элементы
    const draggables = document.querySelectorAll('.module-card[draggable="true"]');
    const dropZones = document.querySelectorAll('.pipeline-slot');

    // Удаляем старые обработчики
    draggables.forEach(drag => {
        drag.removeEventListener('dragstart', handleDragStart);
        drag.removeEventListener('dragend', handleDragEnd);
        drag.addEventListener('dragstart', handleDragStart);
        drag.addEventListener('dragend', handleDragEnd);
    });

    dropZones.forEach(zone => {
        zone.removeEventListener('dragover', handleDragOver);
        zone.removeEventListener('dragleave', handleDragLeave);
        zone.removeEventListener('drop', handleDrop);
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('dragleave', handleDragLeave);
        zone.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    draggedModule = {
        id: e.target.closest('.module-card').getAttribute('data-id'),
        name: e.target.closest('.module-card').getAttribute('data-name'),
        type: e.target.closest('.module-card').getAttribute('data-type')
    };
    e.target.closest('.module-card').classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    if (e.target.closest('.module-card')) {
        e.target.closest('.module-card').classList.remove('dragging');
    }
    draggedModule = null;
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const slot = e.target.closest('.pipeline-slot');
    if (slot) slot.classList.add('dragover');
}

function handleDragLeave(e) {
    const slot = e.target.closest('.pipeline-slot');
    if (slot) slot.classList.remove('dragover');
}

async function handleDrop(e) {
    e.preventDefault();
    const slot = e.target.closest('.pipeline-slot');
    if (slot) slot.classList.remove('dragover');

    if (!draggedModule || !slot) return;

    const acceptType = slot.dataset.accept;

    // Проверяем совместимость типа
    if (acceptType !== draggedModule.type) {
        showNotification(`❌ Модуль "${draggedModule.name}" не подходит для слота "${acceptType}"`, 'error');
        return;
    }

    // Вызываем API для замены модуля
    if (api) {
        try {
            const result = await api.switch_module(acceptType, draggedModule.id);
            if (result.success) {
                showNotification(`✅ Модуль "${draggedModule.name}" установлен в слот ${acceptType}`, 'success');
                // Обновляем pipeline
                const currentPipeline = await api.get_current_pipeline();
                updatePipelineSlots(currentPipeline);
                // Обновляем библиотеку модулей (помечаем, что модуль используется)
                const availableModules = await api.get_available_modules();
                updateModulesLibrary(availableModules);
            } else {
                showNotification(`❌ Ошибка: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Ошибка при замене модуля:', error);
            showNotification('❌ Ошибка при замене модуля', 'error');
        }
    } else {
        // Демо-режим
        showNotification(`🔄 Демо: модуль "${draggedModule.name}" перемещен в слот ${acceptType}`, 'info');
        updatePipelineSlots({
            [acceptType]: {
                id: draggedModule.id,
                name: draggedModule.name,
                type: draggedModule.type,
                icon: '🔧',
                description: 'Активен'
            }
        });
    }
}

function showMockModules() {
    const libraryContainer = document.querySelector('.modules-library');
    const slots = document.querySelectorAll('.pipeline-slot');

    // Мок библиотеки модулей
    if (libraryContainer) {
        const mockModules = [
            { name: "Porcupine", type: "activation", icon: "🎙", desc: "Wake-word detection" },
            { name: "Vosk Detector", type: "activation", icon: "🎙", desc: "Vosk wake-word" },
            { name: "Vosk STT", type: "stt", icon: "🧠", desc: "Speech recognition" },
            { name: "RuleBased NLU", type: "nlp", icon: "🤖", desc: "Intent recognition" },
            { name: "spaCy NLU", type: "nlp", icon: "🧠", desc: "Semantic analysis" },
            { name: "pyttsx3 TTS", type: "tts", icon: "🔊", desc: "Speech synthesis" }
        ];

        const panelTitle = libraryContainer.querySelector('.panel-title');
        libraryContainer.innerHTML = '';
        if (panelTitle) libraryContainer.appendChild(panelTitle);

        mockModules.forEach(module => {
            let iconColor = 'purple';
            if (module.type === 'stt') iconColor = 'green';
            if (module.type === 'tts') iconColor = 'blue';
            if (module.type === 'nlp') iconColor = 'red';

            const moduleCard = document.createElement('div');
            moduleCard.className = 'module-card';
            moduleCard.setAttribute('draggable', 'true');
            moduleCard.setAttribute('data-type', module.type);
            moduleCard.setAttribute('data-name', module.name);
            moduleCard.innerHTML = `
                <div class="module-icon ${iconColor}">${module.icon}</div>
                <div class="module-info">
                    <div class="module-name">${module.name}</div>
                    <div class="module-desc">${module.desc}</div>
                </div>
                <div class="module-type">${module.type.toUpperCase()}</div>
            `;
            libraryContainer.appendChild(moduleCard);
        });

        setupDragAndDrop();
    }

    // Мок pipeline слотов
    if (slots.length >= 4) {
        const mockPipeline = {
            activation: { name: "Porcupine", type: "activation", icon: "🎙", description: "Слушает 'computer'" },
            stt: { name: "Vosk STT", type: "stt", icon: "🧠", description: "Модель: ru-small" },
            nlp: { name: "RuleBased NLU", type: "nlp", icon: "🤖", description: "34 правила" },
            tts: { name: "pyttsx3", type: "tts", icon: "🔊", description: "Голосовые ответы" }
        };
        updatePipelineSlots(mockPipeline);
    }
}

// Добавляем обработчик переключения на вкладку модулей
// В функцию setupTabs добавить:
// else if (tabId === "modulesTab" && api) await refreshModulesTab();

// Обновляем функцию setupTabs
function setupTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabs = document.querySelectorAll(".tab");

    navItems.forEach(item => {
        item.addEventListener("click", async () => {
            navItems.forEach(nav => nav.classList.remove("active"));
            tabs.forEach(tab => tab.classList.remove("active"));

            item.classList.add("active");
            const tabId = item.dataset.tab;
            const activeTab = document.getElementById(tabId);
            if (activeTab) activeTab.classList.add("active");

            if (tabId === "homeTab" && api) await loadAllData();
            else if (tabId === "logsTab" && api) await refreshLogsTab();
            else if (tabId === "commandsTab" && api) await refreshCommandsTab();
            else if (tabId === "modulesTab" && api) await refreshModulesTab();  // <-- ДОБАВИТЬ ЭТУ СТРОКУ
        });
    });
}

// ========== ВКЛАДКА МОДУЛИ - ИСПРАВЛЕННАЯ ВЕРСИЯ ==========

async function handleDrop(e) {
    e.preventDefault();
    const slot = e.target.closest('.pipeline-slot');
    if (slot) slot.classList.remove('dragover');

    if (!draggedModule || !slot) return;

    const acceptType = slot.dataset.accept;

    if (acceptType !== draggedModule.type) {
        showNotification(`❌ Модуль "${draggedModule.name}" не подходит для слота "${acceptType}"`, 'error');
        return;
    }

    if (api) {
        try {
            showNotification(`🔄 Замена модуля "${draggedModule.name}"...`, 'info');

            const result = await api.switch_module(acceptType, draggedModule.id);

            console.log('Результат замены:', result);

            if (result && result.success) {
                showNotification(`✅ ${result.message || 'Модуль успешно заменен'}`, 'success');

                // Показываем индикатор загрузки в слоте
                const slotContent = slot.querySelector('.slot-content');
                if (slotContent) {
                    slotContent.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #a78bfa;">
                            🔄 Замена модуля...
                        </div>
                    `;
                }

                // Ждем немного и обновляем pipeline
                setTimeout(async () => {
                    try {
                        // Получаем обновленный pipeline
                        const currentPipeline = await api.get_current_pipeline();
                        console.log('Обновленный pipeline:', currentPipeline);
                        updatePipelineSlots(currentPipeline);

                        // Также обновляем библиотеку (чтобы подсветить активный модуль)
                        const availableModules = await api.get_available_modules();
                        updateModulesLibrary(availableModules);

                        showNotification(`✅ Модуль "${draggedModule.name}" активен`, 'success');
                    } catch (err) {
                        console.error('Ошибка обновления UI:', err);
                        // Force reload страницы модулей
                        await refreshModulesTab();
                    }
                }, 500);

            } else {
                const errorMsg = result?.message || result?.error || 'Неизвестная ошибка';
                showNotification(`❌ ${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('Ошибка при замене модуля:', error);
            showNotification(`❌ Ошибка: ${error.message}`, 'error');
        }
    } else {
        // Демо-режим
        showNotification(`🔄 Демо: модуль "${draggedModule.name}" перемещен в слот ${acceptType}`, 'info');
        const mockPipeline = {
            activation: { name: "Porcupine", type: "activation", icon: "🎙", description: "Слушает 'computer'" },
            stt: { name: "Vosk STT", type: "stt", icon: "🧠", description: "Модель: ru-small" },
            nlp: { name: "RuleBased NLU", type: "nlp", icon: "🤖", description: "34 правила" },
            tts: { name: "pyttsx3", type: "tts", icon: "🔊", description: "Голосовые ответы" }
        };
        mockPipeline[acceptType] = {
            id: draggedModule.id,
            name: draggedModule.name,
            type: draggedModule.type,
            icon: '🔧',
            description: 'Активен (демо)'
        };
        updatePipelineSlots(mockPipeline);
    }
}

// Обновленная функция updatePipelineSlots с лучшей обработкой
function updatePipelineSlots(pipeline) {
    const slots = document.querySelectorAll('.pipeline-slot');

    slots.forEach(slot => {
        const acceptType = slot.dataset.accept;
        const slotContent = slot.querySelector('.slot-content');
        const slotLabel = slot.querySelector('.slot-label');

        if (!slotContent) return;

        let moduleData = null;
        if (acceptType === 'activation' && pipeline.activation) moduleData = pipeline.activation;
        if (acceptType === 'stt' && pipeline.stt) moduleData = pipeline.stt;
        if (acceptType === 'nlp' && pipeline.nlp) moduleData = pipeline.nlp;
        if (acceptType === 'tts' && pipeline.tts) moduleData = pipeline.tts;

        if (moduleData) {
            let iconColor = 'purple';
            if (moduleData.type === 'stt') iconColor = 'green';
            if (moduleData.type === 'tts') iconColor = 'blue';
            if (moduleData.type === 'nlp') iconColor = 'red';

            // Форматируем имя для отображения
            let displayName = moduleData.name || moduleData.id || 'Модуль';
            if (displayName.length > 20) displayName = displayName.substring(0, 20);

            slotContent.innerHTML = `
                <div class="module-card active-module" style="cursor: default; background: rgba(124,58,237,0.15); margin: 0; border: 1px solid rgba(124,58,237,0.3);">
                    <div class="module-icon ${iconColor}" style="width: 40px; height: 40px;">
                        ${moduleData.icon || '🔧'}
                    </div>
                    <div class="module-info">
                        <div class="module-name" style="font-size: 14px; font-weight: 600;">${escapeHtml(displayName)}</div>
                        <div class="module-desc" style="font-size: 11px;">${escapeHtml(moduleData.description || 'Активен')}</div>
                    </div>
                    <div class="module-type" style="background: rgba(34,197,94,0.15); color: #22c55e;">
                        ✅ АКТИВЕН
                    </div>
                </div>
            `;
        } else {
            slotContent.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #94a3b8; border: 2px dashed rgba(255,255,255,0.1); border-radius: 12px;">
                    📦 Перетащите модуль сюда
                </div>
            `;
        }
    });
}

// Функция для принудительного обновления вкладки модулей
async function forceRefreshModulesTab() {
    console.log('🔄 Принудительное обновление вкладки Модули...');

    if (!api) {
        showMockModules();
        return;
    }

    try {
        // Показываем индикатор загрузки
        const modulesTab = document.getElementById('modulesTab');
        if (modulesTab) {
            modulesTab.style.opacity = '0.5';
        }

        const availableModules = await api.get_available_modules();
        const currentPipeline = await api.get_current_pipeline();

        updateModulesLibrary(availableModules);
        updatePipelineSlots(currentPipeline);
        setupDragAndDrop();

        if (modulesTab) {
            modulesTab.style.opacity = '1';
        }

        console.log('✅ Вкладка Модули обновлена');
    } catch (error) {
        console.error('Ошибка принудительного обновления:', error);
        if (modulesTab) modulesTab.style.opacity = '1';
    }
}

// Обновляем обработчик переключения на вкладку модулей
function setupTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabs = document.querySelectorAll(".tab");

    navItems.forEach(item => {
        item.addEventListener("click", async () => {
            navItems.forEach(nav => nav.classList.remove("active"));
            tabs.forEach(tab => tab.classList.remove("active"));

            item.classList.add("active");
            const tabId = item.dataset.tab;
            const activeTab = document.getElementById(tabId);
            if (activeTab) activeTab.classList.add("active");

            if (tabId === "homeTab" && api) {
                await loadAllData();
            } else if (tabId === "logsTab" && api) {
                await refreshLogsTab();
            } else if (tabId === "commandsTab" && api) {
                await refreshCommandsTab();
            } else if (tabId === "modulesTab") {
                // Принудительное обновление при переключении
                await forceRefreshModulesTab();
            }
        });
    });
}

// ========== АНИМАЦИЯ МИКРОФОНА ==========

// ========== АНИМАЦИЯ МИКРОФОНА (оптимизированная) ==========

function updateMicrophoneAnimation(state, isActive = true) {
    const micCore = document.querySelector('.mic-core');
    const micRing = document.querySelector('.mic-ring');
    const listeningBadge = document.querySelector('.listening-badge');
    const micIconImg = document.querySelector('.mic-icon img');
    const micIconSvg = document.querySelector('.mic-icon svg');
    const micIcon = micIconSvg || micIconImg;

    // Цвета для разных состояний
    const colors = {
        idle: {
            core: 'radial-gradient(circle, rgba(59,130,246,0.25), rgba(59,130,246,0.05) 60%, transparent)',
            ring: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent 70%)',
            shadow: '0 0 40px rgba(59,130,246,0.25)',
            ringColor: '#3b82f6',
            badge: 'Ожидание...',
            badgeColor: '#3b82f6',
            iconColor: '#3b82f6'
        },
        listening: {
            core: 'radial-gradient(circle, rgba(34,197,94,0.35), rgba(34,197,94,0.08) 60%, transparent)',
            ring: 'radial-gradient(circle, rgba(34,197,94,0.25), transparent 70%)',
            shadow: '0 0 50px rgba(34,197,94,0.5)',
            ringColor: '#22c55e',
            badge: '🎤 Слушаю...',
            badgeColor: '#22c55e',
            iconColor: '#22c55e'
        },
        processing: {
            core: 'radial-gradient(circle, rgba(168,85,247,0.35), rgba(168,85,247,0.08) 60%, transparent)',
            ring: 'radial-gradient(circle, rgba(168,85,247,0.25), transparent 70%)',
            shadow: '0 0 50px rgba(168,85,247,0.5)',
            ringColor: '#a855f7',
            badge: '🔄 Обработка...',
            badgeColor: '#a855f7',
            iconColor: '#a855f7'
        },
        inactive: {
            core: 'radial-gradient(circle, rgba(239,68,68,0.25), rgba(239,68,68,0.05) 60%, transparent)',
            ring: 'radial-gradient(circle, rgba(239,68,68,0.15), transparent 70%)',
            shadow: '0 0 40px rgba(239,68,68,0.25)',
            ringColor: '#ef4444',
            badge: '⏸️ Остановлен',
            badgeColor: '#ef4444',
            iconColor: '#ef4444'
        }
    };

    let currentState = state;
    if (!isActive) currentState = 'inactive';

    const colorSet = colors[currentState] || colors.idle;

    // Обновляем mic-core
    if (micCore) {
        micCore.style.background = colorSet.core;
        micCore.style.boxShadow = colorSet.shadow;
        micCore.style.transition = 'all 0.15s ease';
    }

    // Обновляем mic-ring
    if (micRing) {
        micRing.style.background = colorSet.ring;

        // Настройка анимации в зависимости от состояния
        if (currentState === 'listening') {
            micRing.style.animation = 'pulse 0.8s infinite';
            micRing.style.opacity = '1';
        } else if (currentState === 'processing') {
            micRing.style.animation = 'pulse 0.4s infinite';
            micRing.style.opacity = '0.9';
        } else if (currentState === 'inactive') {
            micRing.style.animation = 'none';
            micRing.style.opacity = '0.3';
        } else {
            micRing.style.animation = 'pulse 2s infinite';
            micRing.style.opacity = '0.5';
        }
    }

    // ========== МЕНЯЕМ ЦВЕТ ИКОНКИ МИКРОФОНА ==========
    if (micIcon) {
        if (micIcon.tagName === 'svg') {
            // Для SVG - меняем stroke и добавляем свечение
            micIcon.style.stroke = colorSet.iconColor;
            micIcon.style.transition = 'all 0.15s ease';

            if (currentState === 'listening') {
                micIcon.style.filter = `drop-shadow(0 0 8px ${colorSet.iconColor})`;
            } else if (currentState === 'processing') {
                micIcon.style.filter = `drop-shadow(0 0 12px ${colorSet.iconColor})`;
            } else {
                micIcon.style.filter = `drop-shadow(0 0 4px ${colorSet.iconColor})`;
            }
        } else if (micIcon.tagName === 'IMG') {
            // Для img - меняем через filter (для PNG/SVG с прозрачностью)
            if (currentState === 'listening') {
                micIcon.style.filter = `brightness(1) drop-shadow(0 0 8px #22c55e)`;
            } else if (currentState === 'processing') {
                micIcon.style.filter = `brightness(1) drop-shadow(0 0 12px #a855f7)`;
            } else if (currentState === 'inactive') {
                micIcon.style.filter = `brightness(0.5) drop-shadow(0 0 4px #ef4444)`;
            } else {
                micIcon.style.filter = `brightness(1) drop-shadow(0 0 4px #3b82f6)`;
            }
        }
    }

    // Обновляем бейдж
    if (listeningBadge) {
        listeningBadge.textContent = colorSet.badge;
        listeningBadge.style.background = `rgba(${currentState === 'listening' ? '34,197,94' : (currentState === 'processing' ? '168,85,247' : (currentState === 'inactive' ? '239,68,68' : '59,130,246'))}, 0.15)`;
        listeningBadge.style.color = colorSet.badgeColor;
        listeningBadge.style.transition = 'all 0.15s ease';

        if (currentState === 'listening') {
            listeningBadge.style.animation = 'pulse-green 0.8s infinite';
        } else {
            listeningBadge.style.animation = 'none';
        }
    }

    // Аудиовизуализатор
    const visualizerBars = document.querySelectorAll('.visualizer-bars span');
    if (visualizerBars.length > 0) {
        if (currentState === 'listening') {
            visualizerBars.forEach((bar, i) => {
                bar.style.animation = `sound-wave 0.6s infinite ease-in-out`;
                bar.style.animationDelay = `${i * 0.05}s`;
                bar.style.background = 'linear-gradient(180deg, #22c55e, #059669)';
                bar.style.opacity = '1';
            });
        } else if (currentState === 'processing') {
            visualizerBars.forEach((bar, i) => {
                bar.style.animation = `sound-wave 0.3s infinite ease-in-out`;
                bar.style.animationDelay = `${i * 0.03}s`;
                bar.style.background = 'linear-gradient(180deg, #a855f7, #7c3aed)';
                bar.style.opacity = '1';
            });
        } else if (currentState === 'inactive') {
            visualizerBars.forEach(bar => {
                bar.style.animation = 'none';
                bar.style.height = '8px';
                bar.style.background = 'linear-gradient(180deg, #ef4444, #b91c1c)';
                bar.style.opacity = '0.3';
            });
        } else {
            visualizerBars.forEach((bar, i) => {
                bar.style.animation = `sound-wave 1.5s infinite ease-in-out`;
                bar.style.animationDelay = `${i * 0.08}s`;
                bar.style.background = 'linear-gradient(180deg, #3b82f6, #1d4ed8)';
                bar.style.opacity = '0.6';
            });
        }
    }
}

// Обновление статуса (без задержки)
async function updateAssistantStatus() {
    if (!api) return;

    try {
        const status = await api.get_status();
        const stateText = await api.get_state_text();

        // Мгновенное обновление анимации
        updateMicrophoneAnimation(status.state, status.is_active);

        const statusSub = document.querySelector('.status-sub');
        if (statusSub) {
            statusSub.textContent = stateText;
        }

        return status;
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
    }
}

// Оптимизированная загрузка данных (с меньшей задержкой)
async function loadAllData() {
    if (!api) return;

    try {
        const status = await api.get_status();
        updateStatusDisplay(status);
        updateMicrophoneAnimation(status.state, status.is_active); // Мгновенно

        const todayStats = await api.get_today_stats();
        updateTodayStats(todayStats);

        const uptime = await api.get_uptime();
        updateUptime(uptime);

        const lastCommand = await api.get_last_command();
        updateLastCommand(lastCommand);

        const pipelineStatus = await api.get_pipeline_status();
        updatePipelineStatus(pipelineStatus);

        const recentCommands = await api.get_recent_commands();
        updateRecentCommands(recentCommands);

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Обновление статуса
function updateStatusDisplay(status) {
    let statusElement = document.querySelector('.status-active');
    if (!statusElement) {
        const statCards = document.querySelectorAll('.stat-card');
        for (let card of statCards) {
            const label = card.querySelector('.stat-label');
            if (label && label.textContent === 'Статус ассистента') {
                statusElement = card.querySelector('.stat-value');
                break;
            }
        }
    }

    if (statusElement) {
        if (status.is_active) {
            statusElement.innerHTML = '● Активен';
            statusElement.style.color = '#22c55e';
        } else {
            statusElement.innerHTML = '● Остановлен';
            statusElement.style.color = '#ef4444';
        }
    }
}

// События от Python для мгновенного обновления
function setupCoreEventListeners() {
    // Слушаем изменения состояния
    window.addEventListener('state_change', (event) => {
        if (event.detail && event.detail.state) {
            console.log('⚡ Состояние:', event.detail.state);
            updateMicrophoneAnimation(event.detail.state, true);

            const statusSub = document.querySelector('.status-sub');
            if (statusSub) {
                statusSub.textContent = getStateText(event.detail.state);
            }
        }
    });

    // Событие пробуждения с эффектом
    window.addEventListener('wake_word', () => {
        const micCore = document.querySelector('.mic-core');
        const micRing = document.querySelector('.mic-ring');

        if (micCore) {
            micCore.style.transform = 'scale(1.15)';
            setTimeout(() => {
                micCore.style.transform = 'scale(1)';
            }, 150);
        }
        if (micRing) {
            micRing.style.animation = 'none';
            setTimeout(() => {
                micRing.style.animation = 'pulse 0.8s infinite';
            }, 50);
        }
    });

    // Событие остановки
    window.addEventListener('assistant_stopped', () => {
        updateMicrophoneAnimation('idle', false);
    });
}

// Уменьшаем интервал автообновления
function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(async () => {
        if (api && document.querySelector('.tab.active')?.id === 'homeTab') {
            try {
                // Обновляем только статус (быстро)
                const status = await api.get_status();
                updateMicrophoneAnimation(status.state, status.is_active);

                // Остальные данные обновляем реже
                const todayStats = await api.get_today_stats();
                updateTodayStats(todayStats);

                const uptime = await api.get_uptime();
                updateUptime(uptime);

                const lastCommand = await api.get_last_command();
                updateLastCommand(lastCommand);
            } catch(e) {
                console.error('Ошибка автообновления:', e);
            }
        }
    }, 2000); // Уменьшил с 3 до 2 секунд
}

// Функция для обновления статуса ассистента (вызывать при изменении состояния)
async function updateAssistantStatus() {
    if (!api) return;

    try {
        const status = await api.get_status();
        const stateText = await api.get_state_text();

        // Обновляем анимацию микрофона
        updateMicrophoneAnimation(status.state, status.is_active);

        // Обновляем текстовый статус
        const statusSub = document.querySelector('.status-sub');
        if (statusSub) {
            statusSub.textContent = stateText;
        }

        return status;
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
    }
}

// Вызываем updateAssistantStatus в loadAllData
async function loadAllData() {
    if (!api) {
        console.error('API не доступен');
        return;
    }

    try {
        console.log('🔄 Загрузка данных...');

        const status = await api.get_status();
        console.log('Статус:', status);
        updateStatusDisplay(status);

        // Обновляем анимацию микрофона
        updateMicrophoneAnimation(status.state, status.is_active);

        const todayStats = await api.get_today_stats();
        console.log('Статистика за сегодня:', todayStats);
        updateTodayStats(todayStats);

        const uptime = await api.get_uptime();
        console.log('Время работы:', uptime);
        updateUptime(uptime);

        const lastCommand = await api.get_last_command();
        console.log('Последняя команда:', lastCommand);
        updateLastCommand(lastCommand);

        const pipelineStatus = await api.get_pipeline_status();
        console.log('Pipeline:', pipelineStatus);
        updatePipelineStatus(pipelineStatus);

        const recentCommands = await api.get_recent_commands();
        console.log('Недавние команды:', recentCommands);
        updateRecentCommands(recentCommands);

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Обновляем функцию updateStatusDisplay
function updateStatusDisplay(status) {
    let statusElement = document.querySelector('.status-active');
    if (!statusElement) {
        const statCards = document.querySelectorAll('.stat-card');
        for (let card of statCards) {
            const label = card.querySelector('.stat-label');
            if (label && label.textContent === 'Статус ассистента') {
                statusElement = card.querySelector('.stat-value');
                break;
            }
        }
    }

    if (statusElement) {
        if (status.is_active) {
            statusElement.innerHTML = '● Активен';
            statusElement.style.color = '#22c55e';
        } else {
            statusElement.innerHTML = '● Остановлен';
            statusElement.style.color = '#ef4444';
        }
    }

    const statusSub = document.querySelector('.status-sub');
    if (statusSub && api) {
        api.get_state_text().then(text => {
            statusSub.textContent = text;
        }).catch(() => {
            statusSub.textContent = getStateText(status.state);
        });
    }

    // Обновляем анимацию микрофона при изменении статуса
    updateMicrophoneAnimation(status.state, status.is_active);
}

// Добавляем CSS для анимации свечения
const micAnimationStyle = document.createElement('style');
micAnimationStyle.textContent = `
    @keyframes pulse-green {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    @keyframes pulse-purple {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    .mic-core {
        transition: all 0.3s ease;
    }

    .mic-ring {
        transition: all 0.3s ease;
    }

    .visualizer-bars span {
        transition: all 0.2s ease;
    }
`;
document.head.appendChild(micAnimationStyle);
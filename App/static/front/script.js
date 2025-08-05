// static/front/script.js

function toggleTheme() {
    document.body.classList.toggle("dark-mode");
    
    // Salva a preferência do usuário
    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");
}

// Função para inicializar o tema baseado na preferência salva
function initializeTheme() {
    const savedTheme = localStorage.getItem("theme");
    
    // Se há preferência salva para light mode, aplica
    if (savedTheme === "light") {
        document.body.classList.remove("dark-mode");
    } else {
        // Mantém dark-mode como padrão (já definido no HTML)
        // Se não há preferência salva ou é dark, salva como dark
        document.body.classList.add("dark-mode");
        localStorage.setItem("theme", "dark");
    }
}


/**
 * Ajusta automaticamente a altura do textarea ao conteúdo.
 */
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
}

// Inicializações após carregar DOM: tema, textarea resize e restauração de scroll
window.addEventListener('DOMContentLoaded', function() {
    // Inicializa o tema baseado na preferência salva
    initializeTheme();
    
    const textarea = document.querySelector('textarea[name="nl_query"]');
    if (textarea) {
        autoResize(textarea);
        textarea.addEventListener('input', function() {
            autoResize(this);
        });
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('query-form').submit();
            }
        });
    }
    
    // Restaurar posição de scroll do chat
    const chatBox = document.getElementById('chat-box');
    const savedScroll = sessionStorage.getItem('chat-scroll');
    if (chatBox && savedScroll !== null) {
        chatBox.scrollTop = parseInt(savedScroll, 10);
    }
    
    // Limpa o campo de input se for uma nova sessão sem histórico
    const historyItems = document.querySelectorAll('.user-query');
    const inputField = document.querySelector('input[name="nl_query"]');
    const urlParams = new URLSearchParams(window.location.search);
    const isNewSession = urlParams.get('new_session') === 'true';
    
    // Se é nova sessão ou não há histórico de mensagens, garante que o campo esteja vazio
    if ((isNewSession || historyItems.length === 0) && inputField) {
        inputField.value = '';
        
        // Force reset para garantir que não há valor persistente
        inputField.setAttribute('value', '');
        
        // Remove o parâmetro da URL para evitar conflitos futuros
        if (isNewSession) {
            const url = new URL(window.location);
            url.searchParams.delete('new_session');
            window.history.replaceState({}, document.title, url.pathname);
        }
    }
    
    // Debug: mostra informações no console
    console.log('Nova sessão:', isNewSession);
    console.log('Histórico encontrado:', historyItems.length);
    console.log('Valor do campo input:', inputField ? inputField.value : 'Campo não encontrado');
});

// Preservar posição de scroll ao sair da página
window.addEventListener('beforeunload', function() {
    const chatBox = document.getElementById('chat-box');
    if (chatBox) {
        sessionStorage.setItem('chat-scroll', chatBox.scrollTop);
    }
});

// JS: Expande/colapsa a sidebar ao passar o mouse
function expandSidebar() {
    document.querySelector('.sidebar').classList.remove('sidebar-collapsed');
}
function collapseSidebar() {
    document.querySelector('.sidebar').classList.add('sidebar-collapsed');
}

// ===== Funções movidas do HTML =====

/**
 * Copia texto para a área de transferência
 */
function copyToClipboard(elementId, btn) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text).then(function() {
        if (btn) {
            const original = btn.innerText;
            btn.innerText = "Copiado!";
            btn.disabled = true;
            setTimeout(function() {
                btn.innerText = original;
                btn.disabled = false;
            }, 350);
        }
    });
}

/**
 * Cria uma nova sessão de chat
 */
function createNewSession() {
    fetch('/api/sessions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({title: null})
    })
    .then(response => response.json())
    .then(data => {
        if (data.session_id) {
            // Redireciona para a página inicial com parâmetro para nova sessão
            window.location.href = '/?new_session=true';
        }
    })
    .catch(error => console.error('Erro ao criar nova sessão:', error));
}

/**
 * Troca para uma sessão específica
 */
function switchSession(sessionId) {
    fetch(`/api/sessions/${sessionId}/switch`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        }
    })
    .catch(error => console.error('Erro ao trocar sessão:', error));
}

/**
 * Deleta uma sessão de chat
 */
function deleteSession(sessionId, event) {
    event.stopPropagation(); // Previne o click no item da sessão
    
    if (confirm('Tem certeza que deseja deletar esta conversa?')) {
        fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        })
        .catch(error => console.error('Erro ao deletar sessão:', error));
    }
}

/**
 * Carrega sessões periodicamente para manter atualizado
 */
function loadSessions() {
    fetch('/api/sessions')
    .then(response => response.json())
    .then(data => {
        const sessionsList = document.getElementById('sessions-list');
        if (sessionsList && data.sessions) {
            // Atualiza apenas se necessário para evitar perda de foco
            const currentCount = sessionsList.children.length;
            if (currentCount !== data.sessions.length) {
                updateSessionsList(data.sessions);
            }
        }
    })
    .catch(error => console.error('Erro ao carregar sessões:', error));
}

/**
 * Atualiza a lista de sessões no DOM
 */
function updateSessionsList(sessions) {
    const sessionsList = document.getElementById('sessions-list');
    const currentSessionId = document.body.getAttribute('data-current-session-id');
    
    sessionsList.innerHTML = '';
    
    sessions.forEach(session => {
        const sessionItem = document.createElement('div');
        sessionItem.className = `session-item${session.id === currentSessionId ? ' active' : ''}`;
        sessionItem.setAttribute('data-session-id', session.id);
        
        const date = new Date(session.last_activity).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        sessionItem.innerHTML = `
            <div class="session-title">${session.title}</div>
            <div class="session-preview">${session.last_message}</div>
            <div class="session-date">${date}</div>
            <div class="session-actions">
                <button class="session-btn delete-btn delete-session-btn" data-session-id="${session.id}" title="Deletar">🗑️</button>
            </div>
        `;
        
        sessionsList.appendChild(sessionItem);
    });
    
    // Reconfigura os event listeners para os novos elementos
    setupSessionItems();
    setupDeleteButtons();
}

/**
 * Inicializa carregamento periódico de sessões
 */
function initSessionsAutoLoad() {
    // Carrega sessões a cada 30 segundos
    setInterval(loadSessions, 30000);
}

// Inicializa o auto-load quando a página carrega
window.addEventListener('DOMContentLoaded', function() {
    initSessionsAutoLoad();
    setupEventListeners();
});

/**
 * Configura todos os event listeners da página
 */
function setupEventListeners() {
    // Botão SQL Generator
    const sqlGeneratorBtn = document.querySelector('.sql-generator-btn');
    if (sqlGeneratorBtn) {
        sqlGeneratorBtn.addEventListener('click', function() {
            window.location.href = '/';
        });
    }

    // Botão criar nova sessão
    const createSessionBtn = document.querySelector('.create-session-btn');
    if (createSessionBtn) {
        createSessionBtn.addEventListener('click', createNewSession);
    }

    // Botão toggle tema
    const toggleThemeBtn = document.querySelector('.toggle-theme-btn');
    if (toggleThemeBtn) {
        toggleThemeBtn.addEventListener('click', toggleTheme);
    }

    // Botões de copiar
    setupCopyButtons();
    
    // Itens de sessão
    setupSessionItems();
    
    // Botões de deletar sessão
    setupDeleteButtons();
}

/**
 * Configura os botões de copiar
 */
function setupCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            copyToClipboard(targetId, this);
        });
    });
}

/**
 * Configura os itens de sessão para navegação
 */
function setupSessionItems() {
    const sessionItems = document.querySelectorAll('.session-item');
    sessionItems.forEach(item => {
        // Remove listener anterior se existir
        item.removeEventListener('click', handleSessionClick);
        item.addEventListener('click', handleSessionClick);
    });
}

/**
 * Handler para clique em item de sessão
 */
function handleSessionClick(event) {
    // Previne execução se clicou em um botão dentro do item
    if (event.target.classList.contains('delete-session-btn')) {
        return;
    }
    
    const sessionId = this.getAttribute('data-session-id');
    if (sessionId) {
        switchSession(sessionId);
    }
}

/**
 * Configura os botões de deletar sessão
 */
function setupDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-session-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.stopPropagation();
            const sessionId = this.getAttribute('data-session-id');
            deleteSession(sessionId, event);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const inputForm = document.getElementById('input-form');
    const userInput = document.getElementById('user-input');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatContainer = document.getElementById('chat-container');
    const reportContainer = document.getElementById('report-container');
    const inputArea = document.querySelector('.input-area');
    const chatHeader = document.getElementById('chat-header');
    const narrativeReport = document.getElementById('narrative-report');
    const historyList = document.getElementById('history-list');

    const API_URL = window.location.origin;

    // ==========================================
    // FUNÇÕES DE HISTÓRICO
    // ==========================================

    async function loadHistory() {
        try {
            const response = await fetch(`${API_URL}/api/history?limit=10`);
            const history = await response.json();
            
            if (history.length === 0) {
                historyList.innerHTML = '<p class="history-empty">Nenhuma conversa ainda</p>';
                return;
            }

            historyList.innerHTML = '';
            history.forEach(chat => {
                const item = document.createElement('a');
                item.className = 'history-item';
                item.href = `${API_URL}/history/${chat.id}`;
                item.innerHTML = `
                    <div class="history-item-title">
                        📊 Relatório #${chat.id}
                    </div>
                    <div class="history-item-date">${chat.created_at}</div>
                `;
                historyList.appendChild(item);
            });
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
            historyList.innerHTML = '<p class="history-empty">Erro ao carregar</p>';
        }
    }

    // Carrega histórico ao iniciar
    loadHistory();

    // ==========================================
    // FUNÇÕES DO CHAT
    // ==========================================

    const addMessage = (text, sender) => {
        const messageRow = document.createElement('div');
        messageRow.classList.add('message-row', `${sender}-message-row`);
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = sender === 'user' ? 'U' : 'D';
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.textContent = text;
        
        messageRow.appendChild(avatar);
        messageRow.appendChild(messageElement);
        chatBox.appendChild(messageRow);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    const startConversation = async () => {
        chatHeader.style.display = 'block';
        chatContainer.style.display = 'block';
        inputArea.style.display = 'block';
        reportContainer.style.display = 'none';
        chatBox.innerHTML = '';
        userInput.disabled = false;

        try {
            const response = await fetch(`${API_URL}/start_conversation`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            addMessage(data.response, 'ai');
        } catch (error) {
            addMessage('Não foi possível conectar ao servidor. Verifique se ele está rodando.', 'ai');
        }
    };

    newChatBtn.addEventListener('click', async () => {
        // Limpa a conversa atual
        await fetch(`${API_URL}/api/clear_conversation`, { method: 'POST' });
        startConversation();
    });

    inputForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userText = userInput.value.trim();
        if (!userText) return;
        
        addMessage(userText, 'user');
        userInput.value = '';

        try {
            const response = await fetch(`${API_URL}/send_message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: userText })
            });
            const data = await response.json();
            addMessage(data.response, 'ai');

            if (data.response.includes("Podemos gerar seu relatório?")) {
                userInput.disabled = true;
                const reportButton = document.createElement('button');
                reportButton.textContent = 'Sim, gerar meu relatório!';
                reportButton.style.cssText = 'padding: 12px 20px; margin: 10px auto; display: block; cursor: pointer; border-radius: 8px; border: none; background: #19c37d; color: white; font-weight: bold; font-size: 1em;';
                reportButton.onclick = generateReport;
                chatBox.appendChild(reportButton);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        } catch (error) {
            addMessage('Ocorreu um erro ao enviar a mensagem.', 'ai');
        }
    });

    const generateReport = async () => {
        addMessage("Gerando seu relatório, um momento...", 'ai');
        try {
            const response = await fetch(`${API_URL}/generate_report`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (data.status === 'success') {
                // Redireciona para a página de relatório
                window.location.href = data.redirect_url;
                
                // Atualiza o histórico na sidebar
                loadHistory();
            } else {
                addMessage('Erro ao gerar relatório.', 'ai');
            }
        } catch (error) {
            addMessage('Ocorreu um erro ao gerar seu relatório.', 'ai');
        }
    };

    // Inicia a conversa automaticamente
    startConversation();
});

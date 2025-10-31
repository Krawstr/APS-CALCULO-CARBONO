// Script principal para index.html (chatbot)
let conversationStarted = false;

document.addEventListener('DOMContentLoaded', function () {
    const inputForm = document.getElementById('input-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const newChatBtn = document.getElementById('new-chat-btn');

    // Iniciar conversa automaticamente
    if (!conversationStarted) {
        startConversation();
    }

    // Enviar mensagem
    if (inputForm) {
        inputForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const message = userInput.value.trim();
            if (!message) return;

            // Adicionar mensagem do usuário à tela
            addMessage(message, 'user');
            userInput.value = '';

            // A lógica de "sim/s" foi removida.
            // Apenas enviamos a mensagem para a IA.
            await sendMessage(message);
        });
    }

    // Novo chat
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function () {
            location.reload();
        });
    }
});

async function startConversation() {
    try {
        const response = await fetch('/start_conversation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        addMessage(data.response, 'bot');
        conversationStarted = true;
    } catch (error) {
        console.error('Erro ao iniciar conversa:', error);
    }
}

async function sendMessage(message) {
    // Referências aos elementos
    const btnContainer = document.getElementById('button-container');
    const inputForm = document.getElementById('input-form');

    // Garante que o input esteja visível e o botão escondido ao enviar
    if (btnContainer) btnContainer.innerHTML = '';
    if (inputForm) inputForm.style.display = 'flex';

    try {
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: message })
        });

        const data = await response.json();
        addMessage(data.response, 'bot');

        // --- LÓGICA DO BOTÃO AQUI ---
        // 1. Verifica se a resposta do BOT foi a frase-chave
        if (data.response && data.response.includes('gerar seu relatório?')) {

            // 2. Esconde o formulário de input
            if (inputForm) inputForm.style.display = 'none';

            // 3. Cria e mostra o botão
            const reportButton = document.createElement('button');
            reportButton.textContent = 'Sim, gerar meu relatório!';
            // Use uma classe do seu CSS, 'submit-button' do form.css ou 'new-chat-button' do style.css
            reportButton.className = 'submit-button';

            // 4. Adiciona o evento de clique para chamar a função de relatório
            reportButton.onclick = function () {
                generateReport(); // Chama sua função existente
                if (btnContainer) btnContainer.innerHTML = ''; // Limpa o botão
            };

            if (btnContainer) btnContainer.appendChild(reportButton);
        }
        // --- FIM DA LÓGICA DO BOTÃO ---

    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        addMessage('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
    }
}

async function generateReport() {
    addMessage('Gerando seu relatório... ⏳', 'bot');

    try {
        const response = await fetch('/generate_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.status === 'success') {
            window.location.href = data.redirect_url;
        } else {
            addMessage('Erro ao gerar relatório. Tente novamente.', 'bot');
        }
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        addMessage('Erro ao gerar relatório. Tente novamente.', 'bot');
    }
}

function addMessage(text, sender) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Dropdown do menu de usuário
function toggleDropdown() {
    document.getElementById('dropdown-menu').classList.toggle('show');
}

// Fechar dropdown ao clicar fora
window.onclick = function (event) {
    if (!event.target.matches('.user-avatar')) {
        const dropdown = document.getElementById('dropdown-menu');
        if (dropdown && dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
        }
    }
}
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

    const API_URL = 'http://127.0.0.1:5000';

    const addMessage = (text, sender) => {
        const messageRow = document.createElement('div');
        messageRow.classList.add('message-row', `${sender}-message-row`);
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = sender === 'user' ? 'U' : 'N';
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
            const response = await fetch(`${API_URL}/start_conversation`, { method: 'POST' });
            const data = await response.json();
            addMessage(data.response, 'ai');
        } catch (error) {
            addMessage('Não foi possível conectar ao servidor. Verifique se ele está rodando.', 'ai');
        }
    };

    newChatBtn.addEventListener('click', startConversation);

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
            const response = await fetch(`${API_URL}/generate_report`, { method: 'POST' });
            const data = await response.json();

            chatHeader.style.display = 'none';
            chatContainer.style.display = 'none';
            inputArea.style.display = 'none';
            reportContainer.style.display = 'block';

            narrativeReport.innerText = data.narrative_report;
            const ctx = document.getElementById('footprint-chart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data.data_for_dashboard.details_kg_co2e),
                    datasets: [{
                        data: Object.values(data.data_for_dashboard.details_kg_co2e),
                        backgroundColor: ['#7e57c2', '#19c37d', '#fbc02d'],
                        borderColor: '#343541',
                        borderWidth: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top', labels: { color: '#ececf1' } },
                        title: { display: true, text: `Total: ${data.data_for_dashboard.total_kg_co2e} kg CO2e`, color: '#ececf1' }
                    }
                }
            });
        } catch (error) {
            addMessage('Ocorreu um erro ao gerar seu relatório.', 'ai');
        }
    };

    startConversation();
});
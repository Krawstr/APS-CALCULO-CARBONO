let conversationStarted = false;

document.addEventListener('DOMContentLoaded', function() {
    const inputForm = document.getElementById('input-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const chatContainer = document.getElementById('chat-container');
    const newChatBtn = document.getElementById('new-chat-btn');
    
    // Iniciar conversa automaticamente
    if (!conversationStarted) {
        startConversation();
    }
    
    // Enviar mensagem
    if (inputForm) {
        inputForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = userInput.value.trim();
            if (!message) return;
            
            // Adicionar mensagem do usuário
            addMessage(message, 'user');
            userInput.value = '';
            
            // Verificar se deve gerar relatório
            if (shouldGenerateReport(message)) {
                await generateReport();
                return;
            }
            
            // Enviar mensagem normal para o bot
            await sendMessage(message);
        });
    }
    
    // Novo chat
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // Inicializar mobile menu
    updateMobileMenu();
});

function shouldGenerateReport(userMessage) {
    const botMessages = Array.from(document.querySelectorAll('.bot-message'));
    const recentBotMessages = botMessages.slice(-3);
    
    const botAskedForReport = recentBotMessages.some(msg => {
        const text = msg.textContent.toLowerCase();
        return (
            (text.includes('gerar') && text.includes('relatório')) ||
            text.includes('quer que eu gere') ||
            text.includes('podemos gerar') ||
            text.includes('vamos gerar') ||
            text.includes('posso gerar') ||
            text.includes('criar o relatório')
        );
    });
    
    if (!botAskedForReport) return false;
    
    const userResponse = userMessage.toLowerCase().trim();
    const positiveResponses = [
        'sim', 's', 'yes', 'y',
        'quero', 'queria', 'gostaria',
        'pode', 'por favor', 'pfv',
        'gera', 'gerar', 'cria', 'criar',
        'ok', 'beleza', 'tá', 'ta',
        'dale', 'bora', 'vamos'
    ];
    
    return positiveResponses.some(keyword => {
        return userResponse === keyword || 
               userResponse.includes(keyword) ||
               userResponse.startsWith(keyword);
    });
}

async function startConversation() {
    try {
        console.log('🚀 Iniciando conversa...');
        const response = await fetch('/start_conversation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        addMessage(data.response, 'bot');
        conversationStarted = true;
        console.log('✅ Conversa iniciada');
    } catch (error) {
        console.error('Erro ao iniciar conversa:', error);
        addMessage('Desculpe, tive um problema ao iniciar. Recarregue a página.', 'bot');
    }
}

async function sendMessage(message) {
    try {
        console.log('💬 Enviando mensagem:', message);
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: message})
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('❌ Erro do servidor:', response.status, errorData);
            
            console.log('🔄 Tentando novamente...');
            const retryResponse = await fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: message})
            });
            
            if (!retryResponse.ok) {
                throw new Error('Erro após retry');
            }
            
            const retryData = await retryResponse.json();
            console.log('✅ Resposta recebida após retry');
            addMessage(retryData.response, 'bot');
            return;
        }
        
        const data = await response.json();
        console.log('✅ Resposta recebida');
        addMessage(data.response, 'bot');
        
    } catch (error) {
        console.error('❌ Erro ao enviar mensagem:', error);
        addMessage('Tive um probleminha aqui... Me diga de novo? 😅', 'bot');
    }
}

async function generateReport() {
    console.log('📊 Iniciando geração de relatório...');
    addMessage('🎉 Gerando seu relatório personalizado... Aguarde um momento!', 'bot');
    
    try {
        const response = await fetch('/generate_report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        console.log('📋 Resposta do servidor:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('❌ Erro ao gerar relatório:', errorData);
            throw new Error('Erro ao gerar relatório');
        }
        
        const data = await response.json();
        console.log('✅ Relatório gerado');
        
        if (data.status === 'success' && data.redirect_url) {
            console.log('🔄 Redirecionando para:', data.redirect_url);
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        } else {
            console.error('❌ Status inválido:', data.status);
            addMessage('Erro ao gerar relatório. Tente novamente ou use a Calculadora Manual.', 'bot');
        }
    } catch (error) {
        console.error('❌ Erro ao gerar relatório:', error);
        addMessage('❌ Desculpe, não consegui gerar o relatório. Tente de novo ou use a Calculadora Manual no menu.', 'bot');
    }
}

function addMessage(text, sender) {
    const chatBox = document.getElementById('chat-box');
    const chatContainer = document.getElementById('chat-container');
    
    if (!chatBox || !chatContainer) {
        console.error('❌ Elementos do chat não encontrados');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    
    chatBox.appendChild(messageDiv);
    
    console.log(`💬 Mensagem adicionada (${sender})`);
    
    setTimeout(() => {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

// === DROPDOWN DO MENU DE USUÁRIO ===
function toggleDropdown() {
    const dropdown = document.getElementById('dropdown-menu');
    if (dropdown) {
        dropdown.classList.toggle('show');
        console.log('🔄 Dropdown toggled');
    }
}

// Fechar dropdown ao clicar fora
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('dropdown-menu');
    const userAvatar = document.querySelector('.user-avatar');
    
    if (dropdown && userAvatar && !dropdown.contains(event.target) && !userAvatar.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// === FUNÇÕES DE SIDEBAR MOBILE ===
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar || !overlay) return;
    
    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
    console.log('🔄 Sidebar toggled');
}

function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar || !overlay) return;
    
    sidebar.classList.remove('show');
    overlay.classList.remove('show');
    console.log('🔄 Sidebar fechado');
}

// Mostrar/esconder botão hamburger baseado no tamanho da tela
function updateMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    if (!menuBtn) return;
    
    if (window.innerWidth <= 768) {
        menuBtn.style.display = 'block';
    } else {
        menuBtn.style.display = 'none';
        closeSidebar();
    }
}

// Executar ao carregar e ao redimensionar
window.addEventListener('DOMContentLoaded', updateMobileMenu);
window.addEventListener('resize', updateMobileMenu);

// Fechar sidebar ao clicar em um link (mobile)
document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('.sidebar a, .sidebar button');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });
});

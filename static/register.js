// Script para register.html
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, email, password})
                });
                
                const data = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (response.ok) {
                    showMessage(data.message, 'success');
                    setTimeout(() => window.location.href = '/login', 2000);
                } else {
                    showMessage(data.error, 'error');
                }
            } catch (error) {
                showMessage('Erro ao cadastrar. Tente novamente.', 'error');
            }
        });
    }
});

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.style.display = 'block';
}

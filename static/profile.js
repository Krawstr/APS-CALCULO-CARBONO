// Script para profile.html
document.addEventListener('DOMContentLoaded', function() {
    // Preview de imagem antes do upload
    const fileUpload = document.getElementById('file-upload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('avatar-preview').src = e.target.result;
                }
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Formulário de atualização de perfil
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const newPassword = document.getElementById('new_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Validar senhas
            if (newPassword && newPassword !== confirmPassword) {
                showMessage('As senhas não coincidem', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('email', document.getElementById('email').value);
            formData.append('current_password', document.getElementById('current_password').value);
            formData.append('new_password', newPassword);
            
            // Adicionar foto se houver
            const fileInput = document.getElementById('file-upload');
            if (fileInput.files[0]) {
                formData.append('profile_picture', fileInput.files[0]);
            }
            
            try {
                const response = await fetch('/profile/update', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage(data.message, 'success');
                    // Limpar campos de senha
                    document.getElementById('current_password').value = '';
                    document.getElementById('new_password').value = '';
                    document.getElementById('confirm_password').value = '';
                } else {
                    showMessage(data.error, 'error');
                }
            } catch (error) {
                showMessage('Erro ao atualizar perfil', 'error');
            }
        });
    }
});

async function deleteProfilePicture() {
    if (!confirm('Tem certeza que deseja remover sua foto de perfil?')) {
        return;
    }
    
    try {
        const response = await fetch('/profile/delete-picture', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(data.message, 'success');
            // Atualizar imagem para avatar padrão
            const avatarPreview = document.getElementById('avatar-preview');
            avatarPreview.src = avatarPreview.getAttribute('data-default-src');
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('Erro ao remover foto', 'error');
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

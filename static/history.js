// Script para history.html
function viewReport(reportId) {
    window.location.href = `/report/${reportId}`;
}

async function deleteReport(reportId) {
    if (!confirm('Tem certeza que deseja deletar este relatório?')) {
        return;
    }
    
    try {
        const response = await fetch(`/report/delete/${reportId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Erro ao deletar relatório');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao deletar relatório');
    }
}

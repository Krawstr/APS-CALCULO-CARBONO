document.addEventListener('DOMContentLoaded', function() {
    const reportDataElement = document.getElementById('report-data');
    
    if (reportDataElement) {
        try {
            const reportData = JSON.parse(reportDataElement.textContent);
            console.log('Dados do relatório carregados:', reportData);
            renderChart(reportData);
            formatNarrativeReport(reportData.narrative_report);
        } catch (error) {
            console.error('Erro ao carregar dados do relatório:', error);
        }
    }
});

function formatNarrativeReport(text) {
    const narrativeDiv = document.getElementById('narrative-report');
    if (!narrativeDiv || !text) return;
    
    // Processar markdown em HTML
    let formatted = text
        // ### Headers (h3)
        .replace(/^### (.+)$/gm, '<h3 style="color: var(--accent-purple); margin: 25px 0 15px 0; font-size: 1.3rem; font-weight: 600;">$1</h3>')
        // ## Headers (h2)
        .replace(/^## (.+)$/gm, '<h2 style="color: var(--accent-green); margin: 30px 0 20px 0; font-size: 1.6rem; font-weight: 700; border-bottom: 2px solid var(--accent-green); padding-bottom: 10px;">$1</h2>')
        // **Bold**
        .replace(/\*\*(.+?)\*\*/g, '<strong style="color: var(--accent-green); font-weight: 600;">$1</strong>')
        // Listas numeradas com título em bold
        .replace(/^(\d+)\.\s+\*\*(.+?)\*\*:\s*(.+)$/gm, '<div style="margin: 15px 0; padding-left: 10px; border-left: 3px solid var(--accent-purple);"><strong style="color: var(--accent-purple); font-size: 1.1rem;">$1. $2:</strong> <span style="display: block; margin-top: 5px; padding-left: 20px;">$3</span></div>')
        // Listas numeradas simples
        .replace(/^(\d+)\.\s+(.+)$/gm, '<div style="margin: 12px 0; padding-left: 10px;"><strong style="color: var(--accent-purple);">$1.</strong> $2</div>')
        // Lista com "-" (bullet points)
        .replace(/^- (.+)$/gm, '<div style="margin: 8px 0; padding-left: 20px;">• $1</div>');
    
    // Processar parágrafos (quebras de linha duplas)
    const paragraphs = formatted.split('\n\n');
    formatted = paragraphs
        .map(para => {
            para = para.trim();
            if (!para) return '';
            // Se já tem tags HTML, não wrap em <p>
            if (para.startsWith('<h') || para.startsWith('<div') || para.startsWith('<strong')) {
                return para;
            }
            return `<p style="margin-bottom: 15px; line-height: 1.8; color: var(--text-primary);">${para}</p>`;
        })
        .join('');
    
    // Quebras de linha simples dentro de parágrafos
    formatted = formatted.replace(/\n/g, '<br>');
    
    narrativeDiv.innerHTML = formatted;
}

function renderChart(reportData) {
    const ctx = document.getElementById('footprint-chart');
    if (!ctx) return;
    
    try {
        const chartDetails = reportData.data_for_dashboard.details_kg_co2e;
        const totalEmissions = reportData.data_for_dashboard.total_kg_co2e;
        
        const labels = {
            'transporte': 'Transporte',
            'energia_eletrica': 'Energia Elétrica',
            'gas_cozinha': 'Gás de Cozinha'
        };
        
        const chartLabels = Object.keys(chartDetails).map(key => labels[key] || key);
        const chartValues = Object.values(chartDetails);
        
        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: chartLabels,
                datasets: [{
                    data: chartValues,
                    backgroundColor: ['#7e57c2', '#19c37d', '#fbc02d'],
                    borderColor: '#2a2b32',
                    borderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { 
                        position: 'top',
                        labels: { 
                            color: '#ececf1',
                            font: { size: 14 },
                            padding: 15
                        } 
                    },
                    title: { 
                        display: true, 
                        text: `Total: ${totalEmissions.toFixed(2)} kg CO2e`, 
                        color: '#ececf1',
                        font: { size: 18, weight: 'bold' },
                        padding: { top: 10, bottom: 20 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const percentage = ((value / totalEmissions) * 100).toFixed(1);
                                return `${label}: ${value.toFixed(2)} kg CO2e (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('Gráfico renderizado com sucesso');
    } catch (error) {
        console.error('Erro ao renderizar gráfico:', error);
    }
}
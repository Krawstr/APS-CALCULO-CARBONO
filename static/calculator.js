// Script para calculator.html (relatório)
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se existe reportData definido no template
    if (typeof reportData !== 'undefined') {
        renderChart(reportData);
    }
});

function renderChart(reportData) {
    const ctx = document.getElementById('footprint-chart');
    if (!ctx) return;
    
    const chartDetails = reportData.data_for_dashboard.details_kg_co2e;
    const totalEmissions = reportData.data_for_dashboard.total_kg_co2e;
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(chartDetails),
            datasets: [{
                data: Object.values(chartDetails),
                backgroundColor: ['#7e57c2', '#19c37d', '#fbc02d', '#ff6384'],
                borderColor: '#2a2b32',
                borderWidth: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { 
                    position: 'top', 
                    labels: { 
                        color: '#ececf1', 
                        font: { size: 14 } 
                    } 
                },
                title: { 
                    display: true, 
                    text: `Total: ${totalEmissions} kg CO2e`, 
                    color: '#ececf1',
                    font: { size: 18 }
                }
            }
        }
    });
}

// Chart.js Configuration Helper for StegoShield

function createChiSquareChart(canvasId, channelData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Red Channel', 'Green Channel', 'Blue Channel'],
            datasets: [{
                label: 'Chi-Square Suspicion %',
                data: [
                    channelData.red.suspicion_percent,
                    channelData.green.suspicion_percent,
                    channelData.blue.suspicion_percent
                ],
                backgroundColor: [
                    'rgba(255, 23, 68, 0.7)',
                    'rgba(0, 230, 118, 0.7)',
                    'rgba(0, 242, 254, 0.7)'
                ],
                borderColor: [
                    '#ff1744',
                    '#00e676',
                    '#00f2fe'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#8a99ad' },
                    grid: { color: '#1f2d4a' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

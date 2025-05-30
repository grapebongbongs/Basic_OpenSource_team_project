function drawAttendanceCharts(chartDataList) {
    chartDataList.forEach(data => {
        const ctx = document.getElementById(`chart-age-${data.age}`).getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['출석', '결석'],
                datasets: [{
                    data: [data.attendance_rate, data.absent_rate],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 99, 132, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: {
                        display: true,
                        text: `${data.age}대 출석률`
                    }
                }
            }
        });
    });
}
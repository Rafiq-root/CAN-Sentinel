// ML Analysis Dashboard Logic with Chart.js visualizations

let scoreChart = null;
let timelineChart = null;
let detectorChart = null;
let ecuHeatmapChart = null;
let ecuPieChart = null;
let canIdBarChart = null;

// color constants
const CHART_COLORS = {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    gray: '#6b7280'
};

let allAlerts = [];

async function loadMLData() {
    try {
        const data = await loadJSON('can_security_data.json');
        
        allAlerts = data.alerts || [];
        
        displayKPIs(data.ids_statistics, allAlerts);
        createDetectorComparisonChart(allAlerts);
        createTimelineChart(allAlerts);
        createScoreDistributionChart(allAlerts);
        createTopAnomaliesTable(allAlerts);
        createECUHeatmap(allAlerts);
        createECUPieChart(allAlerts);
        createCANIdBarChart(allAlerts);
        
        updateTimestamp();
        showSuccess('ML data refreshed');
    } catch (error) {
        console.error('Error loading ML data:', error);
        showError('Failed to load ML data');
    }
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
}

function displayKPIs(stats, alerts) {
    // ML-specific alerts
    const mlAlerts = alerts.filter(a => a.detector === 4 || a.detector === 5);
    
    // Average anomaly score
    const avgScore = mlAlerts.length > 0
        ? (mlAlerts.reduce((sum, a) => {
            const match = a.description.match(/score:\s*([-\d.]+)/);
            return sum + (match ? parseFloat(match[1]) : 0);
        }, 0) / mlAlerts.length).toFixed(3)
        : 'N/A';
    
    // Detection rate
    const detectionRate = stats.frames_analyzed > 0
        ? ((stats.attacks_detected / stats.frames_analyzed) * 100).toFixed(1)
        : '0.0';
    
    document.getElementById('kpi-accuracy').textContent = detectionRate + '%';
    document.getElementById('kpi-frames').textContent = formatNumber(stats.frames_analyzed);
    document.getElementById('kpi-ml-detections').textContent = formatNumber(mlAlerts.length);
    document.getElementById('kpi-avg-score').textContent = avgScore;
}

function createDetectorComparisonChart(alerts) {
    const ctx = document.getElementById('detectorChart');
    if (!ctx) return;
    
    const detectorCounts = {
        'ID Whitelist': 0,
        'Frequency': 0,
        'Payload': 0,
        'Bus Load': 0,
        'ML Anomaly': 0
    };
    
    const detectorMap = {
        0: 'ID Whitelist',
        1: 'Frequency',
        2: 'Payload',
        3: 'Bus Load',
        4: 'ML Anomaly',
        5: 'ML Anomaly'
    };
    
    alerts.forEach(alert => {
        const name = detectorMap[alert.detector];
        if (name) detectorCounts[name]++;
    });
    
    if (detectorChart) detectorChart.destroy();
    
    detectorChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(detectorCounts),
            datasets: [{
                data: Object.values(detectorCounts),
                backgroundColor: [
    CHART_COLORS.danger,
    CHART_COLORS.warning,
    CHART_COLORS.info,
    CHART_COLORS.primary,
    CHART_COLORS.secondary
                ],
                borderWidth: 3,
                borderColor: '#1e3c72'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        color: '#fff', 
                        font: { size: 12 },
                        padding: 15
                    }
                },
                title: {
                    display: false
                }
            }
        }
    });
}

function createTimelineChart(alerts) {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;
    
    const cycleGroups = {};
    alerts.forEach(alert => {
        if (!cycleGroups[alert.cycle]) {
            cycleGroups[alert.cycle] = { ml: 0, rule: 0 };
        }
        if (alert.detector === 4 || alert.detector === 5) {
            cycleGroups[alert.cycle].ml++;
        } else {
            cycleGroups[alert.cycle].rule++;
        }
    });
    
    const cycles = Object.keys(cycleGroups).sort((a, b) => parseInt(a) - parseInt(b));
    const mlData = cycles.map(c => cycleGroups[c].ml);
    const ruleData = cycles.map(c => cycleGroups[c].rule);
    
    if (timelineChart) timelineChart.destroy();
    
    timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cycles,
            datasets: [
                {
                    label: 'ML Detection',
                    data: mlData,
                    backgroundColor: 'rgba(162, 155, 254, 0.8)',
                    borderColor: '#a29bfe',
                    borderWidth: 2
                },
                {
                    label: 'Rule-Based',
                    data: ruleData,
                    backgroundColor: 'rgba(254, 202, 87, 0.8)',
                    borderColor: '#feca57',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#fff' }
                }
            }
        }
    });
}

function createScoreDistributionChart(alerts) {
    const ctx = document.getElementById('scoreChart');
    if (!ctx) return;
    
    const mlAlerts = alerts.filter(a => a.description.includes('score:'));
    const scores = mlAlerts.map(a => {
        const match = a.description.match(/score:\s*([-\d.]+)/);
        return match ? parseFloat(match[1]) : null;
    }).filter(s => s !== null);
    
    if (scores.length === 0) return;
    
    const bins = [-20, -15, -10, -5, -2, -1, 0];
    const binCounts = bins.map((min, i) => {
        const max = i < bins.length - 1 ? bins[i + 1] : Infinity;
        return scores.filter(s => s >= min && s < max).length;
    });
    
    const binLabels = bins.map((min, i) => {
        const max = i < bins.length - 1 ? bins[i + 1] : '+';
        return `${min} to ${max}`;
    });
    
    if (scoreChart) scoreChart.destroy();
    
    scoreChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Number of Detections',
                data: binCounts,
                backgroundColor: [
                    'rgba(244, 67, 54, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(254, 202, 87, 0.8)',
                    'rgba(79, 195, 247, 0.8)',
                    'rgba(76, 175, 80, 0.8)',
                    'rgba(76, 175, 80, 0.6)',
                    'rgba(76, 175, 80, 0.4)'
                ],
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Lower scores indicate more suspicious behavior',
                    color: '#b0bec5',
                    font: { size: 13 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

function createTopAnomaliesTable(alerts) {
    const mlAlerts = alerts.filter(a => a.description.includes('score:'));
    
    // Extract scores and sort
    const alertsWithScores = mlAlerts.map(a => {
        const match = a.description.match(/score:\s*([-\d.]+)/);
        return {
            ...a,
            score: match ? parseFloat(match[1]) : 0
        };
    }).sort((a, b) => a.score - b.score);
    
    const top10 = alertsWithScores.slice(0, 10);
    
    const tbody = document.getElementById('anomaly-table-body');
    if (top10.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No ML anomalies detected</td></tr>';
        return;
    }
    
    let html = '';
    top10.forEach((alert, index) => {
        const scoreClass = alert.score < -10 ? 'score-extreme' :
                          alert.score < -5 ? 'score-high' :
                          alert.score < -2 ? 'score-medium' : 'score-low';
        
        html += `
            <tr>
                <td><strong>#${index + 1}</strong></td>
                <td><code>${alert.can_id}</code></td>
                <td>${alert.cycle}</td>
                <td><span class="score-badge ${scoreClass}">${alert.score.toFixed(3)}</span></td>
                <td>${alert.severity}</td>
                <td style="font-size: 0.9em;">${alert.description}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function createECUHeatmap(alerts) {
    const ctx = document.getElementById('ecuHeatmapChart');
    if (!ctx) return;
    
    // Group by CAN ID and cycle
    const heatmapData = {};
    alerts.forEach(alert => {
        if (!heatmapData[alert.can_id]) {
            heatmapData[alert.can_id] = {};
        }
        heatmapData[alert.can_id][alert.cycle] = (heatmapData[alert.can_id][alert.cycle] || 0) + 1;
    });
    
    // Create bubble chart data
    const bubbles = [];
    Object.keys(heatmapData).forEach(canId => {
        Object.keys(heatmapData[canId]).forEach(cycle => {
            bubbles.push({
                x: parseInt(cycle),
                y: canId,
                r: Math.min(heatmapData[canId][cycle] * 3, 20)
            });
        });
    });
    
    if (ecuHeatmapChart) ecuHeatmapChart.destroy();
    
    ecuHeatmapChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Anomalies',
                data: bubbles,
                backgroundColor: 'rgba(244, 67, 54, 0.6)',
                borderColor: '#f44336',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Bubble size represents number of anomalies',
                    color: '#b0bec5',
                    font: { size: 13 }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Cycle',
                        color: '#fff'
                    },
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'CAN ID',
                        color: '#fff'
                    },
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

function createECUPieChart(alerts) {
    const ctx = document.getElementById('ecuPieChart');
    if (!ctx) return;
    
    const canIdCounts = {};
    alerts.forEach(alert => {
        canIdCounts[alert.can_id] = (canIdCounts[alert.can_id] || 0) + 1;
    });
    
    if (ecuPieChart) ecuPieChart.destroy();
    
    ecuPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(canIdCounts),
            datasets: [{
                data: Object.values(canIdCounts),
                backgroundColor: [
                    '#ff6b6b',
                    '#feca57',
                    '#48dbfb',
                    '#4fc3f7',
                    '#a29bfe',
                    '#6c5ce7'
                ],
                borderWidth: 3,
                borderColor: '#1e3c72'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#fff', padding: 10 }
                }
            }
        }
    });
}

function createCANIdBarChart(alerts) {
    const ctx = document.getElementById('canIdBarChart');
    if (!ctx) return;
    
    const mlAlerts = alerts.filter(a => a.description.includes('score:'));
    
    // Group by CAN ID and calculate average score
    const canIdScores = {};
    mlAlerts.forEach(a => {
        const match = a.description.match(/score:\s*([-\d.]+)/);
        const score = match ? parseFloat(match[1]) : 0;
        
        if (!canIdScores[a.can_id]) {
            canIdScores[a.can_id] = { sum: 0, count: 0 };
        }
        canIdScores[a.can_id].sum += score;
        canIdScores[a.can_id].count++;
    });
    
    const canIds = Object.keys(canIdScores);
    const avgScores = canIds.map(id => canIdScores[id].sum / canIdScores[id].count);
    
    if (canIdBarChart) canIdBarChart.destroy();
    
    canIdBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: canIds,
            datasets: [{
                label: 'Avg Anomaly Score',
                data: avgScores,
                backgroundColor: 'rgba(79, 195, 247, 0.8)',
                borderColor: '#4fc3f7',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

// Load data on page load
window.onload = loadMLData;
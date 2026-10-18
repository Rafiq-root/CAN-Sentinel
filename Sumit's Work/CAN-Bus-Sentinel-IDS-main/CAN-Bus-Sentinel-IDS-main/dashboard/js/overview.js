// Security Dashboard Overview

let threatTimelineChart = null;
let attackTypeChart = null;

// Live clock
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour12: false });
    document.getElementById('live-clock').textContent = timeString;
}
setInterval(updateClock, 1000);
updateClock();

// Load dashboard data
async function loadDashboardData() {
    try {
        const data = await loadJSON('can_security_data.json');
        
        displayKPIs(data);
        createThreatTimelineChart(data.alerts);
        createAttackTypeChart(data.attack_statistics);
        displayRecentAlerts(data.alerts);
        
        updateTimestamp();
        showSuccess('Dashboard updated');
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

function displayKPIs(data) {
    // Total frames
    document.getElementById('kpi-total-frames').textContent = 
        formatNumber(data.statistics.total_frames);
    
    // Threats detected
    const threats = data.ids_statistics.attacks_detected;
    document.getElementById('kpi-threats').textContent = formatNumber(threats);
    document.getElementById('kpi-threats-change').textContent = 
        `${threats} active threats`;
    
    // Detection rate
    const rate = data.statistics.total_frames > 0
        ? ((threats / data.statistics.total_frames) * 100).toFixed(1)
        : '0.0';
    document.getElementById('kpi-detection-rate').textContent = rate + '%';
    
    // System health (all ECUs active)
    const activeECUs = data.ecus.filter(e => e.active).length;
    const totalECUs = data.ecus.length;
    const health = ((activeECUs / totalECUs) * 100).toFixed(0);
    document.getElementById('kpi-health').textContent = health + '%';
}

function createThreatTimelineChart(alerts) {
    const ctx = document.getElementById('threatTimelineChart');
    if (!ctx) return;
    
    // Group by cycle
    const cycleGroups = {};
    alerts.forEach(alert => {
        cycleGroups[alert.cycle] = (cycleGroups[alert.cycle] || 0) + 1;
    });
    
    const cycles = Object.keys(cycleGroups).sort((a, b) => parseInt(a) - parseInt(b));
    const counts = cycles.map(c => cycleGroups[c]);
    
    if (threatTimelineChart) threatTimelineChart.destroy();
    
    threatTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: cycles,
            datasets: [{
                label: 'Threats Detected',
                data: counts,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
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
                    beginAtZero: true,
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: '#374151' }
                }
            }
        }
    });
}

function createAttackTypeChart(attackStats) {
    const ctx = document.getElementById('attackTypeChart');
    if (!ctx) return;
    
    if (attackTypeChart) attackTypeChart.destroy();
    
    attackTypeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Fuzzing Attacks', 'DoS Flood', 'Injection Attacks'],
            datasets: [{
                data: [
                    attackStats.fuzzing_frames,
                    attackStats.dos_frames,
                    attackStats.injection_frames
                ],
                backgroundColor: [
                    '#f59e0b',
                    '#ef4444',
                    '#8b5cf6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e5e7eb',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

function displayRecentAlerts(alerts) {
    const tbody = document.getElementById('alerts-table-body');
    
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">No alerts detected</td></tr>';
        return;
    }
    
    // Sort by cycle desc, take last 10
    const recent = [...alerts].sort((a, b) => b.cycle - a.cycle).slice(0, 10);
    
    const detectorNames = {
        0: 'ID Whitelist',
        1: 'Frequency',
        2: 'Payload',
        3: 'Bus Load',
        4: 'ML Anomaly',
        5: 'ML Statistical'
    };
    
    const attackTypes = {
        1: 'Fuzzing',
        2: 'DoS Flood',
        3: 'Replay',
        4: 'Injection',
        5: 'Masquerade'
    };
    
    let html = '';
    recent.forEach(alert => {
        const severityClass = alert.severity.toLowerCase();
        const confidence = (alert.confidence * 100).toFixed(0);
        
        html += `
            <tr>
                <td class="monospace">${new Date().toLocaleTimeString()}</td>
                <td><span class="badge badge-${severityClass}">${alert.severity}</span></td>
                <td class="monospace">${alert.can_id}</td>
                <td>${detectorNames[alert.detector] || 'Unknown'}</td>
                <td>${attackTypes[alert.suspected_attack] || 'Unknown'}</td>
                <td>${confidence}%</td>
                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${alert.description}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Load on page load
window.onload = loadDashboardData;
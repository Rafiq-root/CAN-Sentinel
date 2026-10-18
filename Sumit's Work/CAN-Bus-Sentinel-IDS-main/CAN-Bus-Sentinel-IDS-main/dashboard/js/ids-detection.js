// IDS Detection Dashboard Logic

// Store all alerts for filtering
let allAlerts = [];

async function loadSecurityData() {
    try {
        const data = await loadJSON('can_security_data.json');
        displayDetectionStats(data.ids_statistics);
        displayAttackSummary(data.attack_statistics);
        
        // Store alerts globally for filtering
        allAlerts = data.alerts || [];
        
        // Populate filters dynamically based on actual data
        populateFilters();
        
        // Display with current filters
        filterAlerts();
        
        updateTimestamp();
        showSuccess('Security data refreshed');
    } catch (error) {
        console.error('Error loading security data:', error);
    }
}

function populateFilters() {
    // Get unique values from alerts
    const severities = new Set();
    const detectors = new Set();
    const attacks = new Set();
    
    allAlerts.forEach(alert => {
        severities.add(alert.severity);
        detectors.add(alert.detector);
        attacks.add(alert.suspected_attack);
    });
    
    // Map names
    const detectorNames = {
        0: 'ID Whitelist',
        1: 'Frequency',
        2: 'Payload',
        3: 'Bus Load',
        4: 'Sequence Anomaly',
        5: 'ML Statistical'
    };
    
    const attackTypes = {
        1: 'Fuzzing Attack',
        2: 'DoS Flood',
        3: 'Replay Attack',
        4: 'Injection Attack',
        5: 'Masquerade'
    };
    
    // Populate severity filter
    const severityFilter = document.getElementById('severity-filter');
    severityFilter.innerHTML = '<option value="all">All Severities</option>';
    Array.from(severities).sort().forEach(severity => {
        severityFilter.innerHTML += `<option value="${severity}">${severity}</option>`;
    });
    
    // Populate detector filter
    const detectorFilter = document.getElementById('detector-filter');
    detectorFilter.innerHTML = '<option value="all">All Detectors</option>';
    Array.from(detectors).sort((a, b) => a - b).forEach(detector => {
        const name = detectorNames[detector] || `Detector ${detector}`;
        detectorFilter.innerHTML += `<option value="${detector}">${name}</option>`;
    });
    
    // Populate attack filter
    const attackFilter = document.getElementById('attack-filter');
    attackFilter.innerHTML = '<option value="all">All Attack Types</option>';
    Array.from(attacks).sort((a, b) => a - b).forEach(attack => {
        const name = attackTypes[attack] || `Attack Type ${attack}`;
        attackFilter.innerHTML += `<option value="${attack}">${name}</option>`;
    });
}

function displayDetectionStats(stats) {
    const detectionRate = stats.frames_analyzed > 0 
        ? (stats.attacks_detected / stats.frames_analyzed * 100).toFixed(1) 
        : 0;
    
    document.getElementById('stat-frames-analyzed').textContent = formatNumber(stats.frames_analyzed);
    document.getElementById('stat-threats-detected').textContent = formatNumber(stats.attacks_detected);
    document.getElementById('stat-detection-rate').textContent = detectionRate + '%';
    document.getElementById('stat-total-alerts').textContent = formatNumber(stats.total_alerts);
}

function displayAttackSummary(attackStats) {
    document.getElementById('attack-fuzzing').textContent = formatNumber(attackStats.fuzzing_frames || 0);
    document.getElementById('attack-dos').textContent = formatNumber(attackStats.dos_frames || 0);
    document.getElementById('attack-injection').textContent = formatNumber(attackStats.injection_frames || 0);
}

function filterAlerts() {
    const severityFilter = document.getElementById('severity-filter').value;
    const detectorFilter = document.getElementById('detector-filter').value;
    const attackFilter = document.getElementById('attack-filter').value;
    
    // Filter alerts based on selections
    let filteredAlerts = allAlerts.filter(alert => {
        const matchSeverity = severityFilter === 'all' || alert.severity === severityFilter;
        const matchDetector = detectorFilter === 'all' || alert.detector === parseInt(detectorFilter);
        const matchAttack = attackFilter === 'all' || alert.suspected_attack === parseInt(attackFilter);
        
        return matchSeverity && matchDetector && matchAttack;
    });
    
    displayAlerts(filteredAlerts);
}

function resetFilters() {
    document.getElementById('severity-filter').value = 'all';
    document.getElementById('detector-filter').value = 'all';
    document.getElementById('attack-filter').value = 'all';
    filterAlerts();
}

function displayAlerts(alerts) {
    const container = document.getElementById('alert-timeline');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="alert-item">No alerts match the current filters</div>';
        return;
    }
    
    // Sort by cycle (most recent first)
    const sortedAlerts = [...alerts].sort((a, b) => b.cycle - a.cycle);
    
    // Take latest 100
    const recentAlerts = sortedAlerts.slice(0, 100);
    
    let html = '';
    
    recentAlerts.forEach(alert => {
        const severityClass = `severity-${alert.severity.toLowerCase()}`;
        const badgeClass = `badge-${alert.severity.toLowerCase()}`;
        
        // Map detector types to readable names
        const detectorNames = {
            0: 'ID Whitelist',
            1: 'Frequency',
            2: 'Payload',
            3: 'Bus Load',
            4: 'Sequence Anomaly',
            5: 'ML Statistical'
        };
        
        const detectorName = detectorNames[alert.detector] || 'Unknown';
        
        // Map attack types to readable names
        const attackTypes = {
            0: 'None',
            1: 'Fuzzing Attack',
            2: 'DoS Flood',
            3: 'Replay Attack',
            4: 'Injection Attack',
            5: 'Masquerade'
        };
        
        const suspectedAttack = attackTypes[alert.suspected_attack] || 'Unknown';
        
        const confidence = (alert.confidence * 100).toFixed(0);
        
        html += `
            <div class="alert-item ${severityClass}">
                <div class="alert-header">
                    <div>
                        <span class="alert-badge ${badgeClass}">${alert.severity}</span>
                        <span class="detector-badge">${detectorName}</span>
                        <span style="color: var(--text-secondary);">Cycle ${alert.cycle}</span>
                    </div>
                    <span style="color: var(--primary-blue);">CAN ID: ${alert.can_id}</span>
                </div>
                <div style="margin-bottom: 10px;">
                    ${alert.description}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85em;">
                    <span style="color: var(--text-secondary);">Suspected: ${suspectedAttack}</span>
                    <span style="color: var(--primary-blue);">Confidence: ${confidence}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load data on page load
window.onload = loadSecurityData;
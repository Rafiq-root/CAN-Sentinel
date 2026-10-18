// Bus Monitor specific logic

// Store all frames for filtering
let allFrames = [];

async function loadData() {
    try {
        const data = await loadJSON('can_security_data.json');
        displayBusStats(data.statistics);
        displayECUStatus(data.ecus);
        
        // Store frames globally for filtering
        allFrames = data.frames || [];
        
        // Populate filters dynamically
        populateMessageFilters();
        
        // Display with current filters
        filterMessages();
        
        updateTimestamp();
        showSuccess('Data refreshed successfully');
    } catch (error) {
        console.error('Error loading bus data:', error);
    }
}

function populateMessageFilters() {
    // Get unique ECUs
    const ecus = new Set();
    
    allFrames.forEach(frame => {
        ecus.add(frame.ecu);
    });
    
    // Populate ECU filter
    const ecuFilter = document.getElementById('ecu-filter');
    ecuFilter.innerHTML = '<option value="all">All ECUs</option>';
    Array.from(ecus).sort().forEach(ecu => {
        ecuFilter.innerHTML += `<option value="${ecu}">${ecu}</option>`;
    });
}

function filterMessages() {
    const ecuFilter = document.getElementById('ecu-filter').value;
    
    // Filter frames by ECU only
    let filteredFrames = allFrames.filter(frame => {
        return ecuFilter === 'all' || frame.ecu === ecuFilter;
    });
    
    displayMessages(filteredFrames);
}

function resetMessageFilters() {
    document.getElementById('ecu-filter').value = 'all';
    filterMessages();
}

function displayBusStats(stats) {
    document.getElementById('stat-total-frames').textContent = formatNumber(stats.total_frames);
    document.getElementById('stat-collisions').textContent = stats.collisions;
    document.getElementById('stat-errors').textContent = stats.errors;
    document.getElementById('stat-dropped').textContent = stats.dropped_frames;
}

function displayECUStatus(ecus) {
    const container = document.getElementById('ecu-status');
    let html = '<table class="data-table"><thead><tr><th>ECU Name</th><th>Status</th><th>Frames Sent</th><th>Frames Received</th></tr></thead><tbody>';
    
    ecus.forEach(ecu => {
        const statusBadge = ecu.active 
            ? '<span class="badge badge-success">Active</span>' 
            : '<span class="badge badge-danger">Inactive</span>';
        
        html += `
            <tr>
                <td><strong>${ecu.name}</strong></td>
                <td>${statusBadge}</td>
                <td class="monospace">${formatNumber(ecu.frames_sent)}</td>
                <td class="monospace">${formatNumber(ecu.frames_received)}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function displayMessages(frames) {
    const container = document.getElementById('message-log');
    
    if (!frames || frames.length === 0) {
        container.innerHTML = '<div class="message-item">No messages match the current filters</div>';
        return;
    }
    
    let html = '';
    
    const recentFrames = frames.slice(-50).reverse();
    
    recentFrames.forEach(frame => {
        const ecuClass = frame.ecu.toLowerCase().includes('engine') ? 'ecu-engine' :
                         frame.ecu.toLowerCase().includes('brake') ? 'ecu-brake' : 'ecu-body';
        
        const dataHex = frame.data.map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ');
        
        html += `
            <div class="message-item ${ecuClass}">
                <strong>${frame.ecu}</strong> | ID: ${frame.id} | DLC: ${frame.dlc} | Data: ${dataHex} | Time: ${frame.timestamp}ms
            </div>
        `;
    });
    
    container.innerHTML = html || '<div class="message-item">No messages available</div>';
}

// Load data on page load
window.onload = loadData;
// Common utility functions for all dashboard pages

function updateTimestamp() {
    const element = document.getElementById('last-updated');
    if (element) {
        const now = new Date();
        element.textContent = 'Last updated: ' + now.toLocaleTimeString();
    }
}

function formatNumber(num) {
    return num.toLocaleString();
}

function formatPercentage(num) {
    return (num * 100).toFixed(2) + '%';
}

function showError(message) {
    console.error(message);
    
    // Create toast notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        padding: 12px 20px;
        background: #ef4444;
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease-out;
        font-size: 14px;
        font-weight: 500;
    `;
    errorDiv.textContent = '⚠ ' + message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    // Create toast notification
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        padding: 12px 20px;
        background: #10b981;
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease-out;
        font-size: 14px;
        font-weight: 500;
    `;
    successDiv.textContent = '✓ ' + message;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => successDiv.remove(), 3000);
}

// Load single JSON file with all data
async function loadJSON(filename) {
    try {
        const response = await fetch(`data/can_security_data.json`);
        if (!response.ok) {
            throw new Error(`Cannot load can_security_data.json`);
        }
        return await response.json();
    } catch (error) {
        showError(`Error loading data: ${error.message}`);
        throw error;
    }
}
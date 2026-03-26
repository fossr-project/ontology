// ==================== TOAST NOTIFICATIONS ====================
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        console.error('Toast container not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// ==================== TAB SWITCHING ====================
function switchTab(tabName) {
    // Remove active class from all tabs and contents
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Add active class to clicked tab
    event.target.classList.add('active');

    // Show corresponding content
    const content = document.getElementById(tabName);
    if (content) {
        content.classList.add('active');
    }
}

// ==================== COLLAPSIBLE ====================
function toggleCollapsible(header) {
    const collapsible = header.closest('.collapsible');
    if (collapsible) {
        collapsible.classList.toggle('open');
    }
}

// ==================== LOADING OVERLAY ====================
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ==================== PROGRESS BAR ====================
function updateProgress(elementId, percent, text) {
    const container = document.getElementById(elementId);
    if (!container) return;

    const fill = container.querySelector('.progress-fill');
    const textEl = container.querySelector('.progress-text span:first-child');
    const percentEl = container.querySelector('.progress-text span:last-child');

    container.classList.add('active');
    if (fill) fill.style.width = percent + '%';
    if (textEl) textEl.textContent = text;
    if (percentEl) percentEl.textContent = Math.round(percent) + '%';

    if (percent >= 100) {
        setTimeout(() => {
            container.classList.remove('active');
        }, 2000);
    }
}

function hideProgress(elementId) {
    const container = document.getElementById(elementId);
    if (container) {
        container.classList.remove('active');
    }
}

// ==================== FILE UPLOAD ====================
async function uploadFileToServer(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload/file', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error);
    }
    return result.filepath;
}

// ==================== UTILITY FUNCTIONS ====================
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ==================== VALIDATION ====================
function validateRequired(value, fieldName) {
    if (!value || value.trim() === '') {
        showToast('Validation Error', `${fieldName} is required`, 'error');
        return false;
    }
    return true;
}

function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        showToast('Validation Error', 'Invalid URL format', 'error');
        return false;
    }
}

// ==================== ERROR HANDLING ====================
function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    const message = error.message || 'An unexpected error occurred';
    showToast('Error', message, 'error');
}

// ==================== CONFIRMATION DIALOGS ====================
function confirmAction(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}

function confirmDangerousAction(message, onConfirm) {
    const confirmed = confirm(`⚠️ DANGEROUS OPERATION\n\n${message}\n\nThis action cannot be undone. Are you absolutely sure?`);
    if (confirmed) {
        const doubleConfirm = confirm('Type YES to confirm this dangerous operation');
        if (doubleConfirm) {
            onConfirm();
        }
    }
}

// ==================== LOCAL STORAGE ====================
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('Error saving to localStorage:', e);
        return false;
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.error('Error loading from localStorage:', e);
        return defaultValue;
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    // Create toast container if it doesn't exist
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create loading overlay if it doesn't exist
    if (!document.getElementById('loadingOverlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }

    console.log('Common JavaScript loaded successfully');
});
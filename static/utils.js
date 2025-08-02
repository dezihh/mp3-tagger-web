/**
 * MP3 Tagger Web - Wiederverwendbare JavaScript Utilities
 * Gemeinsame Funktionen für Progress-Controller, API-Calls und UI-Updates
 */

/* === PROGRESS CONTROLLER FACTORY === */
function createUniversalProgressController(config = {}) {
    const defaults = {
        title: '💾 Tags werden gespeichert...',
        overlayId: 'saveProgressOverlay',
        fillId: 'saveProgressFill',
        textId: 'saveProgressText',
        statusId: 'saveProgressStatus',
        titleSelector: '.save-progress-title'
    };
    
    const settings = { ...defaults, ...config };
    
    return {
        show: (title = settings.title) => {
            const overlay = document.getElementById(settings.overlayId);
            const progressTitle = document.querySelector(settings.titleSelector);
            
            if (progressTitle) progressTitle.innerHTML = title;
            overlay.classList.add('show');
            
            const progressFill = document.getElementById(settings.fillId);
            const progressText = document.getElementById(settings.textId);
            const progressStatus = document.getElementById(settings.statusId);
            
            progressFill.style.width = '0%';
            progressText.textContent = 'Initialisierung...';
            progressStatus.textContent = '';
        },
        
        updateProgress: (percent, text, status = '') => {
            const progressFill = document.getElementById(settings.fillId);
            const progressText = document.getElementById(settings.textId);
            const progressStatus = document.getElementById(settings.statusId);
            
            progressFill.style.width = `${percent}%`;
            progressText.textContent = text;
            if (status) progressStatus.textContent = status;
        },
        
        hide: () => {
            const overlay = document.getElementById(settings.overlayId);
            const progressTitle = document.querySelector(settings.titleSelector);
            const progressStatus = document.getElementById(settings.statusId);
            
            overlay.classList.remove('show');
            
            // Reset nach kurzer Verzögerung
            setTimeout(() => {
                if (progressTitle) progressTitle.innerHTML = defaults.title;
                if (progressStatus) progressStatus.style.color = '#27ae60';
            }, 300);
        }
    };
}

/* === API CALL UTILITIES === */
async function makeApiCall(endpoint, options = {}) {
    const config = {
        method: options.method || 'GET',
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
    };
    
    if (options.body && config.method !== 'GET') {
        config.body = options.body;
    }
    
    try {
        const response = await fetch(endpoint, config);
        const result = await response.json();
        return result; // Return data directly for simpler usage
    } catch (error) {
        console.error(`API-Fehler bei ${endpoint}:`, error);
        throw error; // Throw to allow catch in calling code
    }
}

/* === FIELD UPDATE UTILITIES === */
function updateInputField(row, selector, value, className = '', title = '') {
    const input = row.querySelector(selector);
    if (input && value) {
        input.value = value;
        if (className) input.classList.add(className);
        if (title) input.setAttribute('title', title);
        return true;
    }
    return false;
}

function updateRecognizedField(row, selector, value, source, fieldType = 'audio') {
    const className = fieldType === 'album' ? 'album-recognized-field' : 'recognized-field';
    const title = fieldType === 'album' ? `Erkannt als Album-Metadaten` : `Erkannt via ${source}`;
    
    return updateInputField(row, selector, value, className, title);
}

/* === VALIDATION UTILITIES === */
function validateNonEmpty(value, fallback = 'Unbekannt') {
    return value && value.trim() ? value.trim() : fallback;
}

function formatTrackNumber(number, digits = 2) {
    return number ? String(number).padStart(digits, '0') : '';
}

/* === DOM UTILITIES === */
function findRowByFilepath(filepath) {
    return document.querySelector(`[data-filepath="${filepath}"]`) ||
           document.querySelector(`[data-filepath*="${filepath.split('/').pop()}"]`);
}

function getSelectedFilePaths() {
    return Array.from(selectedFiles);
}

/* === USER MESSAGING SYSTEM ===
 * Ersetzt alert() mit benutzerfreundlichen Auto-Close-Popups
 */
function showUserMessage(message, type = 'info', duration = 4000) {
    createToastNotification(message, type, duration);
}

function createToastNotification(message, type = 'info', duration = 4000) {
    // Toast-Container erstellen falls nicht vorhanden
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Toast-Element erstellen
    const toast = document.createElement('div');
    const icon = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
    
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Toast hinzufügen
    toastContainer.appendChild(toast);
    
    // Animation einblenden
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Automatisch ausblenden
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
    
    return toast;
}

/* === ERROR HANDLING === */
function handleApiError(error, context = 'API-Operation') {
    console.error(`Fehler bei ${context}:`, error);
    showUserMessage(`Fehler bei ${context}: ${error.message || error}`, 'error');
}

function handleAsyncOperation(operation, progressController, context = 'Operation') {
    return operation
        .catch(error => {
            handleApiError(error, context);
            progressController.updateProgress(100, '', `❌ Fehler bei ${context}`);
            document.getElementById('saveProgressStatus').style.color = '#e74c3c';
            setTimeout(() => progressController.hide(), 3000);
        });
}

/* === EXPORT FÜR WIEDERVERWENDUNG === */
window.MP3TaggerUtils = {
    createUniversalProgressController,
    makeApiCall,
    updateInputField,
    updateRecognizedField,
    validateNonEmpty,
    formatTrackNumber,
    findRowByFilepath,
    getSelectedFilePaths,
    showUserMessage,
    handleApiError,
    handleAsyncOperation
};

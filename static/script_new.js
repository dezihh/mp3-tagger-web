/**
 * MP3 Tagger - JavaScript für neue UI nach README Spezifikation
 */

// Global variables
let fileData = {};
let currentAudio = null;

/**
 * Initialisierung der Datei-Tabelle
 */
function initializeFileTable() {
    console.log('Initialisiere File Table...');
    
    // Checkbox Event Listeners
    setupCheckboxEvents();
    
    // Input Change Listeners für Metadaten
    setupMetadataInputs();
    
    // Tooltip Setup
    setupTooltips();
    
    // Keyboard Shortcuts
    setupKeyboardShortcuts();
    
    console.log('File Table initialisiert');
}

/**
 * Checkbox Events Setup
 */
function setupCheckboxEvents() {
    // Directory Checkboxes
    document.querySelectorAll('.directory-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const dirPath = this.dataset.dir;
            const isChecked = this.checked;
            
            // Alle Dateien in diesem Verzeichnis markieren/demarkieren
            document.querySelectorAll(`tr[data-file-path^="${dirPath}"] .file-checkbox`).forEach(fileCheckbox => {
                fileCheckbox.checked = isChecked;
            });
        });
    });
    
    // File Checkboxes
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateDirectoryCheckboxes);
    });
}

/**
 * Update Directory Checkboxes basierend auf File Selections
 */
function updateDirectoryCheckboxes() {
    document.querySelectorAll('.directory-checkbox').forEach(dirCheckbox => {
        const dirPath = dirCheckbox.dataset.dir;
        const fileCheckboxes = document.querySelectorAll(`tr[data-file-path^="${dirPath}"] .file-checkbox`);
        const checkedFiles = document.querySelectorAll(`tr[data-file-path^="${dirPath}"] .file-checkbox:checked`);
        
        if (checkedFiles.length === 0) {
            dirCheckbox.checked = false;
            dirCheckbox.indeterminate = false;
        } else if (checkedFiles.length === fileCheckboxes.length) {
            dirCheckbox.checked = true;
            dirCheckbox.indeterminate = false;
        } else {
            dirCheckbox.checked = false;
            dirCheckbox.indeterminate = true;
        }
    });
}

/**
 * Metadaten Input Setup
 */
function setupMetadataInputs() {
    document.querySelectorAll('.metadata-input, .track-input').forEach(input => {
        input.addEventListener('change', function() {
            const filePath = this.dataset.file;
            const field = this.dataset.field;
            const value = this.value;
            
            // Speichere Änderung
            if (!fileData[filePath]) {
                fileData[filePath] = {};
            }
            fileData[filePath][field] = value;
            
            console.log(`Metadaten geändert: ${filePath} - ${field}: ${value}`);
        });
    });
}

/**
 * Tooltip Setup
 */
function setupTooltips() {
    document.addEventListener('mouseover', function(e) {
        if (e.target.hasAttribute('title')) {
            showTooltip(e.target, e.target.getAttribute('title'));
        }
    });
    
    document.addEventListener('mouseout', function(e) {
        if (e.target.hasAttribute('title')) {
            hideTooltip();
        }
    });
}

/**
 * Keyboard Shortcuts Setup
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+A für alle markieren
        if (e.ctrlKey && e.key === 'a') {
            e.preventDefault();
            selectAll();
        }
        
        // ESC für Modals schließen
        if (e.key === 'Escape') {
            closeAllModals();
        }
        
        // Space für Play/Pause (wenn Audio Player offen)
        if (e.key === ' ' && currentAudio) {
            e.preventDefault();
            if (currentAudio.paused) {
                currentAudio.play();
            } else {
                currentAudio.pause();
            }
        }
    });
}

/**
 * Alle markieren
 */
function selectAll() {
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
    document.querySelectorAll('.directory-checkbox').forEach(checkbox => {
        checkbox.checked = true;
        checkbox.indeterminate = false;
    });
    console.log('Alle Dateien markiert');
}

/**
 * Alle abwählen
 */
function selectNone() {
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.querySelectorAll('.directory-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        checkbox.indeterminate = false;
    });
    console.log('Alle Dateien abgewählt');
}

/**
 * Nach Verzeichnis markieren
 */
function selectByDirectory() {
    const directories = document.querySelectorAll('.directory-section');
    if (directories.length === 0) return;
    
    // Zeige Modal für Verzeichnis-Auswahl
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    const content = document.createElement('div');
    content.className = 'modal-content';
    
    const header = document.createElement('div');
    header.className = 'modal-header';
    header.innerHTML = `
        <h3>Verzeichnis auswählen</h3>
        <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
    `;
    
    const body = document.createElement('div');
    body.className = 'modal-body';
    
    directories.forEach((dir, index) => {
        const dirPath = dir.dataset.directory;
        const fileCount = dir.querySelectorAll('.file-checkbox').length;
        
        const button = document.createElement('button');
        button.className = 'btn btn-secondary';
        button.style.margin = '5px';
        button.style.display = 'block';
        button.style.width = '100%';
        button.textContent = `${dirPath} (${fileCount} Dateien)`;
        button.onclick = function() {
            document.querySelector(`input[data-dir="${dirPath}"]`).click();
            modal.remove();
        };
        
        body.appendChild(button);
    });
    
    content.appendChild(header);
    content.appendChild(body);
    modal.appendChild(content);
    document.body.appendChild(modal);
}

/**
 * Audio abspielen
 */
function playAudio(filePath) {
    console.log('Spiele Audio ab:', filePath);
    
    const modal = document.getElementById('audio-player-modal');
    const audioPlayer = document.getElementById('audio-player');
    const audioInfo = document.getElementById('audio-info');
    
    // Setze Audio Source - vollständiger Pfad wird direkt verwendet
    // filePath ist bereits der vollständige absolute Pfad
    audioPlayer.src = `/static/audio${filePath}`;
    console.log('Audio URL:', audioPlayer.src);
    
    // Update Audio Info
    const filename = filePath.split('/').pop();
    const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
    
    if (row) {
        // Versuche zuerst Eingabefelder (erweiterte Ansicht), dann span-Elemente (erste Ansicht)
        const artistInput = row.querySelector('.metadata-input[data-field="artist"]');
        const titleInput = row.querySelector('.metadata-input[data-field="title"]');
        const albumInput = row.querySelector('.metadata-input[data-field="album"]');
        
        const artistSpan = row.querySelector('.col-artist .current-value');
        const titleSpan = row.querySelector('.col-title .current-value');
        const albumSpan = row.querySelector('.col-album .current-value');
        
        const artist = (artistInput?.value || artistSpan?.textContent || 'Unbekannt').trim();
        const title = (titleInput?.value || titleSpan?.textContent || 'Unbekannt').trim();
        const album = (albumInput?.value || albumSpan?.textContent || 'Unbekannt').trim();
        
        audioInfo.innerHTML = `
            <div class="audio-track-info">
                <h4>${title}</h4>
                <p><strong>Artist:</strong> ${artist}</p>
                <p><strong>Album:</strong> ${album}</p>
                <p><strong>Datei:</strong> ${filename}</p>
                <p><strong>Pfad:</strong> ${filePath}</p>
            </div>
        `;
    }
    
    currentAudio = audioPlayer;
    modal.style.display = 'block';
    
    // Auto-play
    audioPlayer.play().catch(err => {
        console.warn('Auto-play fehlgeschlagen:', err);
    });
}

/**
 * Audio Player schließen
 */
function closeAudioPlayer() {
    const modal = document.getElementById('audio-player-modal');
    const audioPlayer = document.getElementById('audio-player');
    
    audioPlayer.pause();
    audioPlayer.src = '';
    modal.style.display = 'none';
    currentAudio = null;
}

/**
 * Audio-Erkennung starten
 */
function recognizeAudio(filePath) {
    console.log('Starte Audio-Erkennung:', filePath);
    
    showProcessingStatus('Audio-Erkennung läuft...');
    
    fetch('/recognize_audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file_path: filePath
        })
    })
    .then(response => response.json())
    .then(data => {
        hideProcessingStatus();
        
        if (data.success) {
            // Update UI mit erkannten Daten
            updateRowWithRecognitionData(filePath, data.result);
            showNotification('Audio erfolgreich erkannt!', 'success');
        } else {
            showNotification('Audio-Erkennung fehlgeschlagen: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideProcessingStatus();
        console.error('Error:', error);
        showNotification('Fehler bei Audio-Erkennung', 'error');
    });
}

/**
 * Row mit Audio-Erkennungs-Daten aktualisieren
 */
function updateRowWithRecognitionData(filePath, result) {
    const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
    if (!row) return;
    
    // Update Input Fields
    if (result.artist) {
        const artistInput = row.querySelector('.metadata-input[data-field="artist"]');
        if (artistInput) artistInput.value = result.artist;
    }
    
    if (result.title) {
        const titleInput = row.querySelector('.metadata-input[data-field="title"]');
        if (titleInput) titleInput.value = result.title;
    }
    
    if (result.album) {
        const albumInput = row.querySelector('.metadata-input[data-field="album"]');
        if (albumInput) albumInput.value = result.album;
    }
    
    // Visual Feedback
    row.style.backgroundColor = '#d4edda';
    setTimeout(() => {
        row.style.backgroundColor = '';
    }, 2000);
}

/**
 * Details anzeigen - lokale Daten aus der Tabelle extrahieren
 */
function showDetails(filePath) {
    console.log('Zeige Details für:', filePath);
    
    const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
    if (!row) {
        showNotification('Datei-Details nicht gefunden', 'error');
        return;
    }
    
    // Extrahiere alle verfügbaren Daten aus der Zeile
    const filename = filePath.split('/').pop();
    const directory = filePath.substring(0, filePath.lastIndexOf('/'));
    
    // IST-Daten (aktuelle ID3-Tags)
    const artistInput = row.querySelector('[data-field="artist"]');
    const titleInput = row.querySelector('[data-field="title"]');
    const albumInput = row.querySelector('[data-field="album"]');
    const genreSpan = row.querySelector('.col-genre .current-value, .col-genre .primary-genre');
    const trackInput = row.querySelector('.track-input');
    
    // Extrahiere Werte
    const artist = artistInput?.value?.trim() || '';
    const title = titleInput?.value?.trim() || '';
    const album = albumInput?.value?.trim() || '';
    const genre = genreSpan?.textContent?.trim() || '';
    const track = trackInput?.value?.trim() || '';
    
    // Cover Status
    const coverStatus = row.querySelector('.cover-status');
    const coverTitle = coverStatus ? coverStatus.getAttribute('title') : 'Unbekannt';
    const coverText = coverStatus ? coverStatus.textContent.trim() : 'Nein';
    
    // Prüfe ob ID3-Tags vorhanden
    const hasAnyId3 = !!(artist || title || album || genre || track);
    
    const details = {
        'Dateiname': filename,
        'Verzeichnis': directory,
        'Vollständiger Pfad': filePath
    };
    
    // Nur ID3-Bereich anzeigen wenn Daten vorhanden
    if (hasAnyId3) {
        details['hr1'] = ''; // HR-Separator
        details['ID3-Tags'] = '📋 Folgende Metadaten gefunden:';
        
        if (artist) details['Artist'] = artist;
        if (title) details['Titel'] = title;
        if (album) details['Album'] = album;
        if (genre) details['Genre'] = genre;
        if (track) details['Track#'] = track;
    }
    
    // Cover-Bereich
    details['hr2'] = ''; // HR-Separator
    details['Cover Status'] = `${coverText} - ${coverTitle}`;
    
    // Cover-Bild anzeigen wenn vorhanden
    if (coverStatus && (coverStatus.classList.contains('cover-internal') || coverStatus.classList.contains('cover-both'))) {
        details['cover-image'] = filePath; // Spezielle Markierung für Cover-Bild
    }
    
    displayDetailsModal(details);
}

/**
 * Details Modal anzeigen - mit HR-Separatoren und Cover-Bild
 */
function displayDetailsModal(details) {
    const modal = document.getElementById('details-modal');
    const content = document.getElementById('details-content');
    
    let html = '<div class="details-container">';
    
    for (const [key, value] of Object.entries(details)) {
        if (key.startsWith('hr')) {
            // HR-Separator
            html += '<hr class="detail-hr">';
        } else if (key === 'cover-image') {
            // Cover-Bild anzeigen - mit Debug-Info
            console.log('Versuche Cover zu laden für:', value);
            html += `
                <div class="detail-cover">
                    <img src="/get_cover_preview?file_path=${encodeURIComponent(value)}" 
                         alt="Album Cover" 
                         class="cover-preview-img"
                         onload="console.log('Cover erfolgreich geladen')"
                         onerror="console.log('Cover-Ladung fehlgeschlagen'); this.style.display='none'">
                </div>
            `;
        } else if (value) {
            // Normaler Eintrag - nur anzeigen wenn Wert vorhanden
            html += `
                <div class="detail-item">
                    <span class="detail-label">${key}:</span>
                    <span class="detail-value">${value}</span>
                </div>
            `;
        }
    }
    
    html += '</div>';
    content.innerHTML = html;
    
    modal.style.display = 'block';
}

/**
 * Details Modal schließen
 */
function closeDetailsModal() {
    document.getElementById('details-modal').style.display = 'none';
}

/**
 * Cover Vorschau anzeigen
 */
function showCoverPreview(filePath) {
    console.log('Zeige Cover für:', filePath);
    
    const modal = document.getElementById('cover-preview-modal');
    const content = document.getElementById('cover-content');
    
    content.innerHTML = `
        <div class="cover-loading">
            <div class="spinner"></div>
            <p>Cover wird geladen...</p>
        </div>
    `;
    
    modal.style.display = 'block';
    
    fetch('/get_cover_preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file_path: filePath
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.cover_url) {
            content.innerHTML = `
                <div class="cover-preview-container">
                    <img src="${data.cover_url}" alt="Cover" style="max-width: 100%; height: auto;">
                    <div class="cover-info">
                        <p><strong>Quelle:</strong> ${data.source || 'Unbekannt'}</p>
                        ${data.size ? `<p><strong>Größe:</strong> ${data.size}</p>` : ''}
                    </div>
                </div>
            `;
        } else {
            content.innerHTML = '<p>Kein Cover verfügbar</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        content.innerHTML = '<p>Fehler beim Laden des Covers</p>';
    });
}

/**
 * Cover Vorschau schließen
 */
function closeCoverPreview() {
    document.getElementById('cover-preview-modal').style.display = 'none';
}

/**
 * Änderungen speichern (für erste Ansicht)
 */
function saveChanges() {
    const selectedFiles = getSelectedFiles();
    
    if (selectedFiles.length === 0) {
        alert('Bitte markieren Sie zuerst Dateien zum Speichern.');
        return;
    }
    
    if (!confirm(`Änderungen für ${selectedFiles.length} Datei(en) speichern?`)) {
        return;
    }
    
    // Sammle alle Metadaten-Änderungen
    const updates = {};
    
    selectedFiles.forEach(filePath => {
        const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
        if (row) {
            updates[filePath] = {
                artist: row.querySelector('[data-field="artist"]')?.value || '',
                title: row.querySelector('[data-field="title"]')?.value || '',
                album: row.querySelector('[data-field="album"]')?.value || '',
                track: row.querySelector('[data-field="track"]')?.value || ''
            };
        }
    });
    
    showProcessingStatus(`Speichere Änderungen für ${selectedFiles.length} Datei(en)...`);
    
    // API Call für Batch-Update
    fetch('/process_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            files: updates
        })
    })
    .then(response => response.json())
    .then(data => {
        hideProcessingStatus();
        
        if (data.success) {
            alert(`Erfolgreich gespeichert:\n${data.processed} Datei(en)`);
            
            if (data.errors && data.errors.length > 0) {
                console.warn('Fehler bei einigen Dateien:', data.errors);
            }
            
            // Optional: Seite neu laden oder Tabelle aktualisieren
            // location.reload();
        } else {
            alert(`Fehler beim Speichern: ${data.error}`);
        }
    })
    .catch(error => {
        hideProcessingStatus();
        console.error('Fehler:', error);
        alert('Fehler beim Speichern der Dateien. Siehe Konsole für Details.');
    });
}

/**
 * Alle markierten Dateien sammeln
 */
function getSelectedFiles() {
    const selectedFiles = [];
    document.querySelectorAll('.file-checkbox:checked').forEach(checkbox => {
        selectedFiles.push(checkbox.dataset.file);
    });
    return selectedFiles;
}

/**
 * Online-Erkennung für markierte Dateien
 */
function performOnlineSearch() {
    const selectedFiles = getSelectedFiles();
    
    if (selectedFiles.length === 0) {
        alert('Bitte markieren Sie zuerst Dateien für die Online-Erkennung.');
        return;
    }
    
    if (!confirm(`Online-Erkennung für ${selectedFiles.length} Datei(en) starten?\n\nDies kann einige Minuten dauern.`)) {
        return;
    }
    
    showProcessingStatus(`Führe Online-Erkennung für ${selectedFiles.length} Datei(en) durch...`);
    
    // Weiterleitung zur erweiterten Analyse
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/enhanced_search';
    
    selectedFiles.forEach(filePath => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'selected_files';
        input.value = filePath;
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
}

/**
 * Markierte verarbeiten
 */
function processSelected() {
    const selectedFiles = [];
    
    document.querySelectorAll('.file-checkbox:checked').forEach(checkbox => {
        const filePath = checkbox.dataset.file;
        const row = checkbox.closest('tr');
        
        const fileInfo = {
            path: filePath,
            artist: row.querySelector('.metadata-input[data-field="artist"]').value,
            title: row.querySelector('.metadata-input[data-field="title"]').value,
            album: row.querySelector('.metadata-input[data-field="album"]').value,
            track: row.querySelector('.track-input').value
        };
        
        selectedFiles.push(fileInfo);
    });
    
    if (selectedFiles.length === 0) {
        showNotification('Keine Dateien ausgewählt', 'warning');
        return;
    }
    
    console.log('Verarbeite Dateien:', selectedFiles);
    showProcessingStatus(`${selectedFiles.length} Datei(en) werden verarbeitet...`);
    
    fetch('/process_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            files: selectedFiles
        })
    })
    .then(response => response.json())
    .then(data => {
        hideProcessingStatus();
        
        if (data.success) {
            showNotification(`${data.processed_count} Dateien erfolgreich verarbeitet!`, 'success');
            // Optionally reload or update UI
        } else {
            showNotification('Fehler bei der Verarbeitung: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideProcessingStatus();
        console.error('Error:', error);
        showNotification('Fehler bei der Verarbeitung', 'error');
    });
}

/**
 * Zurück zur Startseite
 */
function goBack() {
    window.location.href = '/';
}

/**
 * Processing Status anzeigen
 */
function showProcessingStatus(message) {
    const status = document.getElementById('processing-status');
    const text = status.querySelector('.status-text');
    text.textContent = message;
    status.style.display = 'block';
}

/**
 * Processing Status verstecken
 */
function hideProcessingStatus() {
    document.getElementById('processing-status').style.display = 'none';
}

/**
 * Tooltip anzeigen
 */
function showTooltip(element, text) {
    const tooltip = document.getElementById('tooltip');
    tooltip.textContent = text;
    tooltip.style.display = 'block';
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 5) + 'px';
}

/**
 * Tooltip verstecken
 */
function hideTooltip() {
    document.getElementById('tooltip').style.display = 'none';
}

/**
 * Notification anzeigen
 */
function showNotification(message, type = 'info') {
    // Erstelle Notification Element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Style
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        z-index: 1000;
        min-width: 300px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;
    
    // Type-specific styling
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#28a745';
            break;
        case 'error':
            notification.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#212529';
            break;
        default:
            notification.style.backgroundColor = '#17a2b8';
    }
    
    document.body.appendChild(notification);
    
    // Auto-remove nach 5 Sekunden
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Alle Modals schließen
 */
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
}

// Modal Click Outside to Close
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
        
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
    }
});

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFileTable);
} else {
    initializeFileTable();
}

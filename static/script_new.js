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
    
    // Track Digits Configuration
    setupTrackDigitsConfig();
    
    // Setup Hover Events
    setupHoverEvents();
    
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
 * Track Digits Configuration Setup
 */
function setupTrackDigitsConfig() {
    const trackDigitsInput = document.getElementById('track-digits');
    const trackExample = document.getElementById('track-example');
    
    if (trackDigitsInput && trackExample) {
        // Update example on change
        trackDigitsInput.addEventListener('input', function() {
            const digits = parseInt(this.value) || 2;
            const example = '1'.padStart(digits, '0');
            trackExample.textContent = `Beispiel: ${example}`;
        });
        
        // Initialize example
        const digits = parseInt(trackDigitsInput.value) || 2;
        const example = '1'.padStart(digits, '0');
        trackExample.textContent = `Beispiel: ${example}`;
    }
}

/**
 * Get current track digits setting
 */
function getTrackDigits() {
    const trackDigitsInput = document.getElementById('track-digits');
    return trackDigitsInput ? parseInt(trackDigitsInput.value) || 2 : 2;
}

/**
 * Hover Events Setup - Alternative zu onclick-Attributen
 */
function setupHoverEvents() {
    console.log('Setup Hover Events...');
    
    // Warte bis DOM vollständig geladen ist
    setTimeout(() => {
        // Finde alle filename-info Elemente und füge Event Listener hinzu
        const filenameElements = document.querySelectorAll('.filename-info');
        console.log('Gefundene filename-info Elemente:', filenameElements.length);
        
        filenameElements.forEach((element, index) => {
            const filePath = element.dataset.filePath;
            console.log(`Setup Hover für Element ${index}:`, filePath, element);
            
            if (filePath) {
                // Entferne alte Event Listener falls vorhanden
                element.removeEventListener('mouseenter', element._hoverEnter);
                element.removeEventListener('mouseleave', element._hoverLeave);
                
                // Neue Event Listener mit Referenz speichern
                element._hoverEnter = function() {
                    console.log('Mouse enter für:', filePath);
                    showDetailsOnHover(filePath);
                };
                
                element._hoverLeave = function() {
                    console.log('Mouse leave');
                    hideDetailsOnHover();
                };
                
                element.addEventListener('mouseenter', element._hoverEnter);
                element.addEventListener('mouseleave', element._hoverLeave);
                
                // Test-Style hinzufügen um zu sehen ob Element gefunden wurde
                element.style.borderBottom = '2px solid #007bff';
            } else {
                console.warn('Kein filePath für Element:', element);
            }
        });
        
        // Fallback: Setup für alle table rows mit data-file-path
        const tableRows = document.querySelectorAll('tr[data-file-path]');
        console.log('Gefundene Table Rows mit data-file-path:', tableRows.length);
        
        tableRows.forEach((row, index) => {
            const filePath = row.dataset.filePath;
            const filenameCell = row.querySelector('.col-filename');
            
            if (filenameCell && filePath) {
                console.log(`Setup Hover für Row ${index}:`, filePath);
                
                filenameCell.style.cursor = 'help';
                filenameCell.style.color = '#007bff';
                filenameCell.style.textDecoration = 'underline';
                
                filenameCell.addEventListener('mouseenter', function() {
                    console.log('Row mouse enter für:', filePath);
                    showDetailsOnHover(filePath);
                });
                
                filenameCell.addEventListener('mouseleave', function() {
                    console.log('Row mouse leave');
                    hideDetailsOnHover();
                });
            }
        });
    }, 1000); // 1 Sekunde warten
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
 * Details beim Hover anzeigen
 */
function showDetailsOnHover(filePath) {
    console.log('showDetailsOnHover aufgerufen mit:', filePath);
    
    // Test: Zeige sofort ein einfaches Modal ohne Timeout
    if (!filePath) {
        console.error('Kein filePath übergeben!');
        return;
    }
    
    // Kurze Verzögerung um zu vermeiden, dass bei schnellem Mouse-over sofort das Modal öffnet
    clearTimeout(window.hoverTimeout);
    window.hoverTimeout = setTimeout(() => {
        console.log('Timeout erreicht, zeige Details für:', filePath);
        showDetails(filePath);
    }, 300); // Verkürzt auf 300ms für schnellere Reaktion
}

/**
 * Details beim Hover verstecken
 */
function hideDetailsOnHover() {
    // Timeout abbrechen falls noch aktiv
    clearTimeout(window.hoverTimeout);
    
    // Modal sofort schließen wenn Hover-Feld verlassen wird
    closeDetailsModal();
}

/**
 * Details anzeigen - lokale Daten aus der Tabelle extrahieren
 */
function showDetails(filePath) {
    console.log('showDetails aufgerufen für:', filePath);
    
    const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
    console.log('Gefundene Zeile:', row);
    
    if (!row) {
        console.error('Keine Zeile gefunden für:', filePath);
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
    
    // Cover-Bild anzeigen wenn vorhanden (inkl. angereicherte Cover)
    const hasInternalCover = coverStatus && (
        coverStatus.classList.contains('cover-internal') || 
        coverStatus.classList.contains('cover-both') ||
        coverStatus.classList.contains('cover-enriched') ||
        (window.enrichedData && window.enrichedData[filePath] && window.enrichedData[filePath].cover_source) ||
        (window.hoverCoverCache && window.hoverCoverCache[filePath] && window.hoverCoverCache[filePath].loaded)
    );
    
    if (hasInternalCover) {
        details['cover-image'] = filePath; // Spezielle Markierung für Cover-Bild
    }
    
    // Angereicherte Daten hinzufügen falls vorhanden
    if (window.enrichedData && window.enrichedData[filePath]) {
        const enriched = window.enrichedData[filePath];
        
        details['hr3'] = ''; // HR-Separator
        details['Angereicherte Daten'] = '🌐 Erweiterte Online-Informationen:';
        
        if (enriched.enriched_genre) {
            details['Erweitertes Genre'] = enriched.enriched_genre;
        }
        
        if (enriched.detailed_genre && enriched.detailed_genre.subgenres) {
            details['Subgenres'] = enriched.detailed_genre.subgenres.join(', ');
        }
        
        if (enriched.mood) {
            details['Stimmung'] = enriched.mood;
        }
        
        if (enriched.era) {
            details['Zeitraum'] = enriched.era;
        }
        
        if (enriched.atmospheric_tags && enriched.atmospheric_tags.length > 0) {
            details['Atmosphäre'] = enriched.atmospheric_tags.join(', ');
        }
        
        if (enriched.similar_artists && enriched.similar_artists.length > 0) {
            details['Ähnlich'] = enriched.similar_artists.slice(0, 3).join(', ');
        }
        
        if (enriched.release_date) {
            details['Erscheinungsdatum'] = enriched.release_date;
        }
        
        if (enriched.musicbrainz_id) {
            details['MusicBrainz ID'] = enriched.musicbrainz_id;
        }
        
        if (enriched.cover_source) {
            details['Cover Quelle'] = enriched.cover_source;
        }
    }
    
    displayDetailsModal(details);
}

/**
 * Details Modal anzeigen - mit HR-Separatoren und Cover-Bild
 */
function displayDetailsModal(details) {
    console.log('displayDetailsModal aufgerufen mit:', details);
    
    const modal = document.getElementById('details-modal');
    const content = document.getElementById('details-content');
    
    console.log('Modal Element:', modal);
    console.log('Content Element:', content);
    
    if (!modal || !content) {
        console.error('Modal oder Content Element nicht gefunden!');
        return;
    }
    
    let html = '<div class="details-container">';
    
    for (const [key, value] of Object.entries(details)) {
        if (key.startsWith('hr')) {
            // HR-Separator
            html += '<hr class="detail-hr">';
        } else if (key === 'cover-image') {
            // Cover-Bild anzeigen - prüfe Cache zuerst
            console.log('Versuche Cover zu laden für:', value);
            
            if (window.hoverCoverCache && window.hoverCoverCache[value] && window.hoverCoverCache[value].loaded) {
                // Verwende vorgeladenes Cover aus Cache
                console.log('Verwende vorgeladenes Cover aus Cache');
                html += `
                    <div class="detail-cover">
                        <img src="${window.hoverCoverCache[value].coverData}" 
                             alt="Album Cover" 
                             class="cover-preview-img"
                             style="max-width: 200px; height: auto;">
                        <p style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            ${Math.round(window.hoverCoverCache[value].size / 1024)} KB (Online Cover)
                        </p>
                    </div>
                `;
            } else {
                // Fallback: Versuche eingebettetes Cover zu laden
                console.log('Lade eingebettetes Cover');
                html += `
                    <div class="detail-cover">
                        <img src="/get_cover_preview?file_path=${encodeURIComponent(value)}" 
                             alt="Album Cover" 
                             class="cover-preview-img"
                             style="max-width: 200px; height: auto;"
                             onload="console.log('Cover erfolgreich geladen')"
                             onerror="console.log('Cover-Ladung fehlgeschlagen'); this.style.display='none'">
                    </div>
                `;
            }
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
    console.log('🔧 saveChanges() aufgerufen');
    const selectedFiles = getSelectedFiles();
    console.log('🔧 Ausgewählte Dateien:', selectedFiles);
    
    if (selectedFiles.length === 0) {
        console.log('🔧 Keine Dateien ausgewählt');
        alert('Bitte markieren Sie zuerst Dateien zum Speichern.');
        return;
    }
    
    if (!confirm(`Änderungen für ${selectedFiles.length} Datei(en) speichern?`)) {
        console.log('🔧 Benutzer hat Speichern abgebrochen');
        return;
    }
    
    console.log('🔧 Sammle Metadaten-Änderungen...');
    // Sammle alle Metadaten-Änderungen
    const updates = [];
    
    selectedFiles.forEach(filePath => {
        const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
        if (row) {
            const updateData = {
                path: filePath,
                artist: row.querySelector('[data-field="artist"]')?.value || '',
                title: row.querySelector('[data-field="title"]')?.value || '',
                album: row.querySelector('[data-field="album"]')?.value || '',
                track: row.querySelector('[data-field="track"]')?.value || ''
            };
            updates.push(updateData);
            console.log(`🔧 Metadaten für ${filePath}:`, updateData);
        } else {
            console.log(`🔧 Keine Zeile gefunden für ${filePath}`);
        }
    });
    
    console.log('🔧 Alle Updates:', updates);
    showProcessingStatus(`Speichere Änderungen für ${selectedFiles.length} Datei(en)...`);
    
    // 1. Erst Metadaten speichern
    saveMetadataUpdates(updates)
        .then(() => {
            // 2. Dann Cover-Auswahlen anwenden
            return applyCoverSelections(selectedFiles);
        })
        .then(() => {
            hideProcessingStatus();
            showNotification(`✅ Alle Änderungen erfolgreich gespeichert!`, 'success');
        })
        .catch(error => {
            hideProcessingStatus();
            console.error('Speicher-Fehler:', error);
            showNotification('Fehler beim Speichern der Änderungen', 'error');
        });
}

/**
 * Metadaten-Updates speichern
 */
function saveMetadataUpdates(updates) {
    console.log('🔧 saveMetadataUpdates() aufgerufen mit:', updates);
    return fetch('/process_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            files: updates
        })
    })
    .then(response => {
        console.log('🔧 Server-Response:', response);
        return response.json();
    })
    .then(data => {
        console.log('🔧 Server-Antwort:', data);
        if (!data.success) {
            throw new Error(data.error || 'Metadaten-Speicherung fehlgeschlagen');
        }
        console.log(`🔧 Metadaten für ${data.processed_count} Dateien gespeichert`);
        return data;
    })
    .catch(error => {
        console.error('🔧 Fehler in saveMetadataUpdates:', error);
        throw error;
    });
}

/**
 * Cover-Auswahlen anwenden
 */
function applyCoverSelections(filePaths) {
    console.log('🔧 applyCoverSelections() aufgerufen mit:', filePaths);
    const promises = [];
    
    // 1. Benutzer-Cover-Auswahlen (für Dateien mit vorhandenem Cover)
    console.log('🔧 Prüfe window.coverSelections:', window.coverSelections);
    if (window.coverSelections) {
        const userCoverPromises = filePaths
            .filter(filePath => window.coverSelections[filePath])
            .map(filePath => {
                const selection = window.coverSelections[filePath];
                console.log(`🔧 Benutzer-Cover-Auswahl für ${filePath}:`, selection);
                
                return fetch('/apply_cover', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_path: filePath,
                        cover_choice: selection.choice,
                        cover_url: selection.url
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log(`Cover ${selection.choice} für ${filePath}: ${data.action}`);
                    } else {
                        console.error(`Cover-Fehler für ${filePath}:`, data.error);
                    }
                });
            });
        
        promises.push(...userCoverPromises);
    }
    
    // 2. Automatische Cover-Einbettung (für Dateien ohne vorhandenes Cover)
    console.log('🔧 Prüfe window.enrichedData:', window.enrichedData);
    if (window.enrichedData) {
        console.log('🔧 window.enrichedData vorhanden, prüfe Dateien...');
        const autoCoverFiles = filePaths
            .filter(filePath => {
                const data = window.enrichedData[filePath];
                console.log(`🔧 Daten für ${filePath}:`, data);
                const hasUrl = data && data.suggested_cover_url;
                const hasNoCover = !data || !data.existing_cover || !data.existing_cover.has_cover;
                
                console.log(`🔧 ${filePath}: hasUrl=${hasUrl}, hasNoCover=${hasNoCover}`);
                if (data && data.suggested_cover_url) {
                    console.log(`🔧 suggested_cover_url: ${data.suggested_cover_url}`);
                }
                if (data && data.existing_cover) {
                    console.log(`🔧 existing_cover:`, data.existing_cover);
                }
                
                if (hasUrl && hasNoCover) {
                    console.log(`🎨 Automatische Cover-Einbettung für: ${filePath}`);
                    console.log(`🎨 Cover URL: ${data.suggested_cover_url}`);
                }
                
                return hasUrl && hasNoCover;
            });
        
        console.log(`🔧 Gefunden ${autoCoverFiles.length} Dateien für automatische Cover-Einbettung`);
        console.log(`🔧 autoCoverFiles:`, autoCoverFiles);
        
        const autoCoverPromises = autoCoverFiles.map(filePath => {
                const data = window.enrichedData[filePath];
                
                console.log(`🔧 Starte automatische Cover-Einbettung für: ${filePath}`);
                console.log(`🔧 Verwende Cover-URL: ${data.suggested_cover_url}`);
                
                return fetch('/apply_cover', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_path: filePath,
                        cover_choice: 'new_cover',
                        cover_url: data.suggested_cover_url
                    })
                })
                .then(response => {
                    console.log(`🔧 Cover-Response für ${filePath}:`, response);
                    return response.json();
                })
                .then(data => {
                    console.log(`🔧 Cover-Antwort für ${filePath}:`, data);
                    if (data.success) {
                        console.log(`✅ Automatisches Cover für ${filePath}: ${data.action}`);
                    } else {
                        console.error(`❌ Auto-Cover-Fehler für ${filePath}:`, data.error);
                    }
                })
                .catch(error => {
                    console.error(`❌ Auto-Cover-Request-Fehler für ${filePath}:`, error);
                });
            });
        
        console.log(`🔧 Cover-Promises erstellt:`, autoCoverPromises);
        promises.push(...autoCoverPromises);
    } else {
        console.log('🔧 Keine window.enrichedData verfügbar');
    }
    
    console.log(`🔧 Gesamt-Promises:`, promises.length);
    if (promises.length === 0) {
        console.log('🔧 Keine Cover-Operationen nötig');
        return Promise.resolve();
    }
    
    return Promise.all(promises);
}

/**
 * Album-Erkennung für komplettes Verzeichnis
 */
function recognizeAlbum(directoryPath) {
    console.log('Starte Album-Erkennung für:', directoryPath);
    
    showProcessingStatus(`🎼 Führe Album-Erkennung durch für: ${directoryPath.split('/').pop()}`);
    
    fetch('/recognize_album', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            directory_path: directoryPath
        })
    })
    .then(response => response.json())
    .then(data => {
        hideProcessingStatus();
        
        if (data.success && data.candidates && data.candidates.length > 0) {
            showAlbumSelectionModal(data.candidates, directoryPath);
        } else if (data.success && data.candidates.length === 0) {
            showNotification('Keine Album-Kandidaten gefunden. Versuchen Sie die einzelne Track-Erkennung.', 'warning');
        } else {
            showNotification(`Album-Erkennung fehlgeschlagen: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        hideProcessingStatus();
        console.error('Album-Erkennung Fehler:', error);
        showNotification('Fehler bei der Album-Erkennung', 'error');
    });
}

/**
 * Zeigt Modal mit Album-Auswahl-Optionen
 */
function showAlbumSelectionModal(candidates, directoryPath) {
    // Erstelle Modal dynamisch
    const modalHtml = `
        <div id="album-selection-modal" class="modal" style="display: block;">
            <div class="modal-content album-selection-content">
                <div class="modal-header">
                    <h3>🎼 Album-Erkennung: Kandidaten gefunden</h3>
                    <span class="close" onclick="closeAlbumSelectionModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <p><strong>Verzeichnis:</strong> ${directoryPath}</p>
                    <p>Bitte wählen Sie das passende Album aus oder verwerfen Sie alle Vorschläge:</p>
                    
                    <div class="album-candidates">
                        ${candidates.map((candidate, index) => `
                            <div class="album-candidate" data-index="${index}">
                                <div class="candidate-info">
                                    <h4>${candidate.album || 'Unbekanntes Album'}</h4>
                                    <p><strong>Artist:</strong> ${candidate.artist || 'Unbekannt'}</p>
                                    <p><strong>Jahr:</strong> ${candidate.date || 'Unbekannt'}</p>
                                    <p><strong>Tracks:</strong> ${candidate.track_count || 'Unbekannt'}</p>
                                    <p><strong>Land:</strong> ${candidate.country || 'Unbekannt'}</p>
                                    <p><strong>Quelle:</strong> ${candidate.source} (Score: ${(candidate.match_score * 100).toFixed(1)}%)</p>
                                </div>
                                <div class="candidate-actions">
                                    <button onclick="applyAlbumCandidate(${index}, '${directoryPath}')" class="btn btn-primary">
                                        ✅ Verwenden
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="modal-footer">
                        <button onclick="closeAlbumSelectionModal()" class="btn btn-secondary">
                            ❌ Alle verwerfen
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Entferne existierendes Modal falls vorhanden
    const existingModal = document.getElementById('album-selection-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Füge neues Modal hinzu
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Speichere Kandidaten für späteren Zugriff
    window.albumCandidates = candidates;
}

/**
 * Wendet ausgewählten Album-Kandidaten an
 */
function applyAlbumCandidate(candidateIndex, directoryPath) {
    const candidate = window.albumCandidates[candidateIndex];
    
    if (!candidate) {
        showNotification('Fehler: Kandidat nicht gefunden', 'error');
        return;
    }
    
    console.log('Wende Album-Kandidat an:', candidate);
    
    showProcessingStatus('Wende Album-Informationen auf alle Dateien im Verzeichnis an...');
    
    // Finde alle Zeilen für dieses Verzeichnis
    const directoryRows = document.querySelectorAll(`tr[data-file-path^="${directoryPath}"]`);
    
    // Sortiere Zeilen nach intelligenter Track-Erkennung
    const rowsWithTrackInfo = Array.from(directoryRows).map(row => {
        const fileName = row.dataset.filePath.split('/').pop();
        const trackNumber = extractTrackNumberFromFilename(fileName);
        return {
            row: row,
            fileName: fileName,
            detectedTrack: trackNumber,
            originalOrder: Array.from(directoryRows).indexOf(row)
        };
    });
    
    // Sortiere: Erst nach erkannter Track-Nummer, dann alphabetisch
    rowsWithTrackInfo.sort((a, b) => {
        if (a.detectedTrack && b.detectedTrack) {
            return a.detectedTrack - b.detectedTrack;
        } else if (a.detectedTrack) {
            return -1;
        } else if (b.detectedTrack) {
            return 1;
        } else {
            return a.fileName.toLowerCase().localeCompare(b.fileName.toLowerCase());
        }
    });
    
    console.log(`Wende Album-Info auf ${rowsWithTrackInfo.length} Dateien an`);
    
    // Wende Album-Info auf alle Dateien an
    rowsWithTrackInfo.forEach((item, index) => {
        const row = item.row;
        const albumInput = row.querySelector('[data-field="album"]');
        const artistInput = row.querySelector('[data-field="artist"]');
        const trackInput = row.querySelector('[data-field="track"]');
        
        if (albumInput && candidate.album) {
            albumInput.value = candidate.album;
        }
        
        if (artistInput && candidate.artist) {
            // Nur setzen wenn Artist-Feld leer ist
            if (!artistInput.value.trim()) {
                artistInput.value = candidate.artist;
            }
        }
        
        // Setze Track-Nummer: Verwende erkannte Nummer oder sequenziell mit konfigurierten Stellen
        if (trackInput) {
            const trackDigits = getTrackDigits();
            let trackNumber;
            if (item.detectedTrack) {
                trackNumber = item.detectedTrack.toString().padStart(trackDigits, '0');
                console.log(`Erkannte Track-Nummer verwendet: ${trackNumber} für ${item.fileName}`);
            } else {
                trackNumber = (index + 1).toString().padStart(trackDigits, '0');
                console.log(`Sequenzielle Track-Nummer gesetzt: ${trackNumber} für ${item.fileName}`);
            }
            trackInput.value = trackNumber;
        }
        
        // Markiere Zeile als geändert
        row.classList.add('album-applied');
        
        // Markiere Checkbox
        const checkbox = row.querySelector('.file-checkbox');
        if (checkbox) {
            checkbox.checked = true;
        }
    });
    
    hideProcessingStatus();
    closeAlbumSelectionModal();
    
    showNotification(`Album-Informationen mit Track-Nummern angewendet: "${candidate.album}" von ${candidate.artist} (${rowsWithTrackInfo.length} Tracks)`, 'success');
}

/**
 * Extrahiert Track-Nummer aus Dateiname
 */
function extractTrackNumberFromFilename(fileName) {
    // Verschiedene Patterns für Track-Nummern
    const patterns = [
        /^(\d+)[\s\-\.]/,           // "01 - Title" oder "01. Title" 
        /^(\d+)[\s]*\-/,            // "01-Title" oder "01 -Title"
        /^\w+\s*-\s*(\d+)/,         // "Artist - 01"
        /(\d+)[\s]*\-[\s]*\w+/,     // "01 - Title"
        /^(\d{2})/,                 // Erste zwei Ziffern
        /[\s\-\.\_](\d{2})[\s\-\.\_]/, // " 01 " oder "-01-" oder ".01."
    ];
    
    for (const pattern of patterns) {
        const match = fileName.match(pattern);
        if (match) {
            const trackNum = parseInt(match[1], 10);
            if (trackNum > 0 && trackNum <= 99) {
                return trackNum;
            }
        }
    }
    
    return null;
}

/**
 * Schließt Album-Auswahl Modal
 */
function closeAlbumSelectionModal() {
    const modal = document.getElementById('album-selection-modal');
    if (modal) {
        modal.remove();
    }
    // Cleanup
    window.albumCandidates = null;
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
 * Datenanreicherung für markierte Dateien
 */
function performDataEnrichment() {
    const selectedFiles = getSelectedFiles();
    
    if (selectedFiles.length === 0) {
        alert('Bitte markieren Sie zuerst Dateien für die Datenanreicherung.');
        return;
    }
    
    if (!confirm(`Datenanreicherung für ${selectedFiles.length} Datei(en) starten?\n\nDies sammelt erweiterte Informationen wie Cover, Genre, MusicBrainz-IDs, Mood, Era etc.\n\nDies kann einige Minuten dauern.`)) {
        return;
    }
    
    showProcessingStatus(`🌐 Führe Datenanreicherung für ${selectedFiles.length} Datei(en) durch...`);
    
    // Sammle aktuelle Metadaten der markierten Dateien
    const filesWithMetadata = [];
    selectedFiles.forEach(filePath => {
        const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
        if (row) {
            filesWithMetadata.push({
                path: filePath,
                artist: row.querySelector('[data-field="artist"]')?.value || '',
                title: row.querySelector('[data-field="title"]')?.value || '',
                album: row.querySelector('[data-field="album"]')?.value || '',
                track: row.querySelector('[data-field="track"]')?.value || ''
            });
        }
    });
    
    // Starte erweiterte Anreicherung mit Progress-Updates
    performEnrichmentWithProgress(filesWithMetadata);
}

/**
 * Führt Datenanreicherung mit detailliertem Progress durch
 */
function performEnrichmentWithProgress(filesWithMetadata) {
    let currentIndex = 0;
    const totalFiles = filesWithMetadata.length;
    let enrichedResults = [];
    
    function processNextFile() {
        if (currentIndex >= totalFiles) {
            // Alle Dateien verarbeitet
            hideProcessingStatus();
            updateUIWithEnrichedData(enrichedResults);
            showNotification(`✅ Datenanreicherung abgeschlossen: ${enrichedResults.length} Dateien erweitert!`, 'success');
            return;
        }
        
        const currentFile = filesWithMetadata[currentIndex];
        const fileName = currentFile.path.split('/').pop();
        const artistTitle = currentFile.artist && currentFile.title ? 
            `${currentFile.artist} - ${currentFile.title}` : fileName;
        
        // Update Progress Status mit aktueller Datei
        updateProcessingStatus(
            `🌐 Anreicherung (${currentIndex + 1}/${totalFiles})`,
            `Verarbeite: ${artistTitle}`,
            Math.round(((currentIndex) / totalFiles) * 100)
        );
        
        // API Call für einzelne Datei
        fetch('/enrich_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                files: [currentFile]
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.enriched_files && data.enriched_files.length > 0) {
                enrichedResults.push(...data.enriched_files);
                
                // Aktualisiere UI für diese Datei sofort
                updateUIWithEnrichedData(data.enriched_files);
            }
            
            currentIndex++;
            // Kurze Pause zwischen Anfragen um Server zu schonen
            setTimeout(processNextFile, 500);
        })
        .catch(error => {
            console.error('Fehler bei Datei:', currentFile.path, error);
            currentIndex++;
            setTimeout(processNextFile, 500);
        });
    }
    
    // Starte Verarbeitung
    processNextFile();
}

/**
 * Aktualisiert die UI mit angereicherten Daten
 */
function updateUIWithEnrichedData(enrichedFiles) {
    enrichedFiles.forEach(fileData => {
        const row = document.querySelector(`tr[data-file-path="${fileData.path}"]`);
        if (!row) return;
        
        console.log('Aktualisiere UI für:', fileData.path, fileData);
        
        // Aktualisiere Basis-Metadaten (kursiv für neue Daten)
        if (fileData.enriched_artist && fileData.enriched_artist !== fileData.original_artist) {
            const artistInput = row.querySelector('[data-field="artist"]');
            if (artistInput) {
                artistInput.value = fileData.enriched_artist;
                artistInput.style.fontStyle = 'italic';
                artistInput.title = `Angereichert: ${fileData.enriched_artist}`;
            }
        }
        
        if (fileData.enriched_title && fileData.enriched_title !== fileData.original_title) {
            const titleInput = row.querySelector('[data-field="title"]');
            if (titleInput) {
                titleInput.value = fileData.enriched_title;
                titleInput.style.fontStyle = 'italic';
                titleInput.title = `Angereichert: ${fileData.enriched_title}`;
            }
        }
        
        if (fileData.enriched_album && fileData.enriched_album !== fileData.original_album) {
            const albumInput = row.querySelector('[data-field="album"]');
            if (albumInput) {
                albumInput.value = fileData.enriched_album;
                albumInput.style.fontStyle = 'italic';
                albumInput.title = `Angereichert: ${fileData.enriched_album}`;
            }
        }
        
        // Aktualisiere Genre (erweiterte Anzeige)
        if (fileData.enriched_genre) {
            const genreContainer = row.querySelector('.genre-container');
            if (genreContainer) {
                let genreDisplay = fileData.enriched_genre;
                
                // Erweiterte Genre-Informationen hinzufügen
                if (fileData.detailed_genre) {
                    genreDisplay += ` (${fileData.detailed_genre.subgenres ? fileData.detailed_genre.subgenres.join(', ') : ''})`;
                }
                
                genreContainer.innerHTML = `
                    <span class="enriched-genre" style="font-style: italic; color: #007bff;" 
                          title="Angereichert: ${genreDisplay}${fileData.mood ? ' | Mood: ' + fileData.mood : ''}${fileData.era ? ' | Era: ' + fileData.era : ''}">
                        ${genreDisplay}
                    </span>
                `;
            }
        }
        
        // Aktualisiere Cover-Status basierend auf vorhandenem Cover und verfügbaren Kandidaten
        if (fileData.cover_preview_available) {
            const coverInfo = row.querySelector('.cover-info');
            if (coverInfo) {
                if (fileData.existing_cover && fileData.existing_cover.has_cover) {
                    // Datei HAT bereits Cover - zeige Auswahl-Option
                    coverInfo.innerHTML = `
                        <span class="cover-status cover-preview" 
                              style="background-color: #fff3cd; color: #856404; cursor: pointer;"
                              onclick="showCoverSelectionModal('${fileData.path}')"
                              title="Klicken für Cover-Auswahl">
                            🎨 AUSWAHL
                        </span>
                    `;
                } else {
                    // Datei hat KEIN Cover, aber Cover verfügbar - zeige "wird hinzugefügt"
                    coverInfo.innerHTML = `
                        <span class="cover-status" 
                              style="background-color: #d4edda; color: #155724;"
                              title="Neues Cover wird automatisch hinzugefügt">
                            🎨 NEU
                        </span>
                    `;
                }
            }
            
            // Lade Cover-Vorschau im Hintergrund für Hover-Funktion
            if (fileData.cover_candidates && fileData.cover_candidates.length > 0) {
                preloadCoverForHover(fileData.path, fileData.cover_candidates[0].url);
            }
        }
        
        // Visual Feedback für angereicherte Zeile
        row.style.backgroundColor = '#e3f2fd';
        row.classList.add('enriched-row');
        
        // Speichere angereicherte Daten für Hover-Details und Cover-Auswahl
        if (!window.enrichedData) {
            window.enrichedData = {};
        }
        window.enrichedData[fileData.path] = {
            enriched_genre: fileData.enriched_genre,
            detailed_genre: fileData.detailed_genre,
            mood: fileData.mood,
            era: fileData.era,
            musicbrainz_id: fileData.musicbrainz_id,
            release_date: fileData.release_date,
            cover_candidates: fileData.cover_candidates || [],
            existing_cover: fileData.existing_cover || {has_cover: false},
            suggested_cover_url: fileData.suggested_cover_url, // Für automatische Einbettung
            atmospheric_tags: fileData.atmospheric_tags || [],
            similar_artists: fileData.similar_artists || []
        };
        
        // Debug: Zeige suggested_cover_url an
        console.log(`🔧 BACKEND-DATEN für ${fileData.path}:`, fileData);
        if (fileData.suggested_cover_url) {
            console.log(`🔧 Suggested Cover URL für ${fileData.path}:`, fileData.suggested_cover_url);
        } else {
            console.log(`🔧 KEINE suggested_cover_url für ${fileData.path} - Wert:`, fileData.suggested_cover_url);
        }
        
        // Timeout für visuelles Feedback
        setTimeout(() => {
            row.style.backgroundColor = '';
        }, 3000);
    });
    
    // Cover-Status direkt aktualisieren ohne Reload
    refreshCoverDisplayForEnrichedFiles(enrichedFiles);
}

/**
 * Aktualisiert Cover-Anzeigen für angereicherte Dateien ohne Reload
 */
function refreshCoverDisplayForEnrichedFiles(enrichedFiles) {
    enrichedFiles.forEach(fileData => {
        const row = document.querySelector(`tr[data-file-path="${fileData.path}"]`);
        if (!row) return;
        
        const coverStatus = row.querySelector('.cover-status');
        if (!coverStatus) return;
        
        if (fileData.cover_preview_available) {
            if (fileData.existing_cover && fileData.existing_cover.has_cover) {
                // Cover-Auswahl für Dateien mit vorhandenem Cover
                coverStatus.classList.remove('cover-none', 'cover-external');
                coverStatus.classList.add('cover-preview');
                
                coverStatus.textContent = '🎨 AUSWAHL';
                coverStatus.setAttribute('title', 'Klicken für Cover-Auswahl');
                coverStatus.style.backgroundColor = '#fff3cd';
                coverStatus.style.color = '#856404';
                coverStatus.style.cursor = 'pointer';
                
                coverStatus.removeAttribute('onclick');
                coverStatus.onclick = () => showCoverSelectionModal(fileData.path);
            } else {
                // Neues Cover für Dateien ohne vorhandenes Cover
                coverStatus.classList.remove('cover-none', 'cover-external', 'cover-preview');
                
                coverStatus.textContent = '🎨 NEU';
                coverStatus.setAttribute('title', 'Neues Cover wird automatisch hinzugefügt');
                coverStatus.style.backgroundColor = '#d4edda';
                coverStatus.style.color = '#155724';
                coverStatus.style.cursor = 'default';
                
                coverStatus.removeAttribute('onclick');
                coverStatus.onclick = null;
            }
            
            // Lade Cover-Vorschau im Hintergrund für Hover-Funktion
            if (fileData.cover_candidates && fileData.cover_candidates.length > 0) {
                preloadCoverForHover(fileData.path, fileData.cover_candidates[0].url);
            }
        }
    });
}

/**
 * Cover-Auswahl Modal anzeigen
 */
function showCoverSelectionModal(filePath) {
    console.log('Zeige Cover-Auswahl für:', filePath);
    
    if (!window.enrichedData || !window.enrichedData[filePath]) {
        showNotification('Keine Cover-Daten verfügbar', 'error');
        return;
    }
    
    const fileData = window.enrichedData[filePath];
    const coverCandidates = fileData.cover_candidates || [];
    const existingCover = fileData.existing_cover || {has_cover: false};
    
    let modalHtml = `
        <div id="cover-selection-modal" class="modal" style="display: block;">
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h3>🎨 Cover-Auswahl für ${filePath.split('/').pop()}</h3>
                    <span class="close" onclick="closeCoverSelectionModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <p>Wählen Sie das gewünschte Cover aus oder behalten Sie das vorhandene bei:</p>
                    
                    <div class="cover-options">
    `;
    
    // Option 1: Vorhandenes Cover (falls vorhanden)
    if (existingCover.has_cover) {
        modalHtml += `
            <div class="cover-option">
                <div class="cover-preview">
                    <img src="/get_cover_preview?file_path=${encodeURIComponent(filePath)}" 
                         alt="Vorhandenes Cover" style="max-width: 200px; height: auto;">
                </div>
                <div class="cover-info">
                    <h4>Vorhandenes Cover</h4>
                    <p><strong>Format:</strong> ${existingCover.format || 'Unbekannt'}</p>
                    <p><strong>Größe:</strong> ${Math.round((existingCover.size || 0) / 1024)} KB</p>
                    <button onclick="selectCover('${filePath}', 'keep_existing')" class="btn btn-secondary">
                        📁 Vorhandenes beibehalten
                    </button>
                </div>
            </div>
        `;
    }
    
    // Option 2: Neue Cover-Kandidaten
    coverCandidates.forEach((candidate, index) => {
        modalHtml += `
            <div class="cover-option">
                <div class="cover-preview" id="preview-${index}">
                    <div class="loading">Cover wird geladen...</div>
                </div>
                <div class="cover-info">
                    <h4>Neues Cover</h4>
                    <p><strong>Quelle:</strong> ${candidate.source}</p>
                    <p><strong>Qualität:</strong> ${candidate.quality}</p>
                    <button onclick="selectCover('${filePath}', 'new_cover', '${candidate.url}')" class="btn btn-primary">
                        ✨ Dieses Cover verwenden
                    </button>
                </div>
            </div>
        `;
    });
    
    // Option 3: Cover entfernen
    if (existingCover.has_cover) {
        modalHtml += `
            <div class="cover-option">
                <div class="cover-preview" style="display: flex; align-items: center; justify-content: center; background: #f8f9fa; border: 2px dashed #dee2e6; height: 200px;">
                    <span style="font-size: 48px; color: #6c757d;">🚫</span>
                </div>
                <div class="cover-info">
                    <h4>Cover entfernen</h4>
                    <p>Alle Cover-Bilder aus der Datei entfernen</p>
                    <button onclick="selectCover('${filePath}', 'remove')" class="btn btn-danger">
                        ❌ Cover entfernen
                    </button>
                </div>
            </div>
        `;
    }
    
    modalHtml += `
                    </div>
                    
                    <div class="modal-footer">
                        <button onclick="closeCoverSelectionModal()" class="btn btn-secondary">
                            Abbrechen
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Entferne existierendes Modal
    const existingModal = document.getElementById('cover-selection-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Füge neues Modal hinzu
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Lade Cover-Vorschauen
    coverCandidates.forEach((candidate, index) => {
        loadCoverPreview(candidate.url, `preview-${index}`);
    });
}

/**
 * Lädt Cover-Vorschau für URL
 */
function loadCoverPreview(coverUrl, containerId) {
    fetch('/preview_cover', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            cover_url: coverUrl
        })
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById(containerId);
        if (container && data.success) {
            container.innerHTML = `
                <img src="${data.cover_data}" alt="Cover Vorschau" style="max-width: 200px; height: auto;">
                <p style="font-size: 0.8em; color: #666;">${Math.round(data.size / 1024)} KB</p>
            `;
        } else if (container) {
            container.innerHTML = '<div class="error">Cover konnte nicht geladen werden</div>';
        }
    })
    .catch(error => {
        console.error('Cover-Vorschau Fehler:', error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="error">Fehler beim Laden</div>';
        }
    });
}

/**
 * Lädt Cover im Hintergrund für Hover-Funktion vor
 */
function preloadCoverForHover(filePath, coverUrl) {
    // Prüfe ob bereits geladen
    if (window.hoverCoverCache && window.hoverCoverCache[filePath]) {
        return;
    }
    
    if (!window.hoverCoverCache) {
        window.hoverCoverCache = {};
    }
    
    // Lade Cover im Hintergrund
    fetch('/preview_cover', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            cover_url: coverUrl
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.hoverCoverCache[filePath] = {
                coverData: data.cover_data,
                size: data.size,
                loaded: true
            };
            console.log(`Cover für ${filePath} vorgeladen`);
        }
    })
    .catch(error => {
        console.error('Cover-Vorladung Fehler:', error);
        window.hoverCoverCache[filePath] = {
            loaded: false,
            error: true
        };
    });
}

/**
 * Cover-Auswahl bestätigen
 */
function selectCover(filePath, coverChoice, coverUrl = null) {
    console.log('Cover ausgewählt:', filePath, coverChoice, coverUrl);
    
    // Speichere Auswahl für späteren Anwendung beim Speichern
    if (!window.coverSelections) {
        window.coverSelections = {};
    }
    
    window.coverSelections[filePath] = {
        choice: coverChoice,
        url: coverUrl
    };
    
    // Update UI
    const row = document.querySelector(`tr[data-file-path="${filePath}"]`);
    if (row) {
        const coverInfo = row.querySelector('.cover-info');
        if (coverInfo) {
            let statusText = '';
            let statusColor = '';
            
            switch(coverChoice) {
                case 'keep_existing':
                    statusText = '📁 BEHALTEN';
                    statusColor = '#6c757d';
                    break;
                case 'new_cover':
                    statusText = '✨ NEUES';
                    statusColor = '#28a745';
                    break;
                case 'remove':
                    statusText = '❌ ENTFERNEN';
                    statusColor = '#dc3545';
                    break;
            }
            
            coverInfo.innerHTML = `
                <span class="cover-status cover-selected" 
                      style="background-color: ${statusColor}; color: white; cursor: pointer;"
                      onclick="showCoverSelectionModal('${filePath}')"
                      title="Cover-Auswahl getroffen - Klicken zum Ändern">
                    ${statusText}
                </span>
            `;
        }
    }
    
    closeCoverSelectionModal();
    showNotification(`Cover-Auswahl gespeichert: ${coverChoice === 'keep_existing' ? 'Vorhandenes beibehalten' : coverChoice === 'new_cover' ? 'Neues Cover' : 'Cover entfernen'}`, 'success');
}

/**
 * Cover-Auswahl Modal schließen
 */
function closeCoverSelectionModal() {
    const modal = document.getElementById('cover-selection-modal');
    if (modal) {
        modal.remove();
    }
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
 * Erweiterte Processing Status Aktualisierung mit Progress und Details
 */
function updateProcessingStatus(mainMessage, detailMessage = '', progressPercent = null) {
    const status = document.getElementById('processing-status');
    const text = status.querySelector('.status-text');
    
    let html = `<div class="status-main">${mainMessage}</div>`;
    
    if (detailMessage) {
        html += `<div class="status-detail" style="font-size: 0.9em; color: #666; margin-top: 5px;">${detailMessage}</div>`;
    }
    
    if (progressPercent !== null) {
        html += `
            <div class="status-progress" style="margin-top: 8px;">
                <div style="background-color: #e0e0e0; border-radius: 10px; height: 6px; overflow: hidden;">
                    <div style="background-color: #007bff; height: 100%; width: ${progressPercent}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="text-align: center; font-size: 0.8em; margin-top: 2px;">${progressPercent}%</div>
            </div>
        `;
    }
    
    text.innerHTML = html;
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

/**
 * Test-Funktion für Modal-Debugging
 * Kann in der Browser-Konsole aufgerufen werden: testModal()
 */
function testModal() {
    console.log('Teste Modal...');
    const modal = document.getElementById('details-modal');
    const content = document.getElementById('details-content');
    
    console.log('Modal gefunden:', modal);
    console.log('Content gefunden:', content);
    
    if (modal && content) {
        content.innerHTML = '<div class="test-content"><h3>TEST MODAL</h3><p>Das Modal funktioniert!</p></div>';
        modal.style.display = 'block';
        console.log('Modal sollte jetzt sichtbar sein');
    } else {
        console.error('Modal oder Content nicht gefunden!');
    }
}

// Mache testModal global verfügbar
window.testModal = testModal;

// Test-Funktion für Speicher-Debugging
function testSaveFunction() {
    console.log('🔧 TEST: testSaveFunction() aufgerufen');
    const selectedFiles = getSelectedFiles();
    console.log('🔧 TEST: Ausgewählte Dateien:', selectedFiles);
    
    if (selectedFiles.length === 0) {
        console.log('🔧 TEST: Keine Dateien ausgewählt - Teste mit erster verfügbarer Datei');
        const firstRow = document.querySelector('tr[data-file-path]');
        if (firstRow) {
            const filePath = firstRow.getAttribute('data-file-path');
            console.log('🔧 TEST: Erste gefundene Datei:', filePath);
            
            // Checkbox markieren
            const checkbox = firstRow.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = true;
                console.log('🔧 TEST: Checkbox markiert');
            }
            
            // Erneut testen
            const newSelection = getSelectedFiles();
            console.log('🔧 TEST: Nach Markierung ausgewählte Dateien:', newSelection);
        }
    }
    
    return selectedFiles;
}

// Mache auch diese Funktion global verfügbar
window.testSaveFunction = testSaveFunction;

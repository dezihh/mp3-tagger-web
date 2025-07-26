document.addEventListener('DOMContentLoaded', function() {
    // Alle Checkboxen für ein Verzeichnis markieren/demarkieren
    const dirCheckboxes = document.querySelectorAll('.dir-checkbox');
    dirCheckboxes.forEach(function(dirCheckbox) {
        dirCheckbox.addEventListener('change', function() {
            const dirPath = this.getAttribute('data-dir');
            const isChecked = this.checked;
            
            // Finde alle Datei-Checkboxen in diesem Verzeichnis
            const dirGroup = this.closest('.directory-group');
            const fileCheckboxes = dirGroup.querySelectorAll('.file-checkbox');
            
            fileCheckboxes.forEach(function(fileCheckbox) {
                fileCheckbox.checked = isChecked;
            });
        });
    });

    // Button für die Anwendung der ausgewählten Änderungen
    const applyButton = document.getElementById('apply-selected');
    if (applyButton) {
        applyButton.addEventListener('click', function() {
            const selectedFiles = [];
            const checkedBoxes = document.querySelectorAll('.file-checkbox:checked');
            
            checkedBoxes.forEach(function(checkbox) {
                selectedFiles.push(checkbox.getAttribute('data-file'));
            });
            
            if (selectedFiles.length === 0) {
                alert('Keine Dateien ausgewählt!');
                return;
            }
            
            // Hier würde normalerweise eine AJAX-Anfrage an den Server gesendet
            // Für jetzt zeigen wir nur eine Bestätigung
            if (confirm(`${selectedFiles.length} Dateien ausgewählt. Tags übernehmen?`)) {
                alert('Funktion noch nicht implementiert - nur Demo.');
            }
        });
    }

    // Tooltip-Funktionalität für Tag-Zellen mit dynamischer Positionierung
    const tagCells = document.querySelectorAll('.tag-cell, .cover-info');
    
    tagCells.forEach(function(cell) {
        cell.addEventListener('mouseenter', function(event) {
            const tooltip = this.querySelector('.tag-tooltip');
            if (tooltip) {
                tooltip.style.display = 'block';
                
                // Dynamische Positionierung basierend auf Mausposition
                positionTooltip(tooltip, event);
            }
        });
        
        cell.addEventListener('mousemove', function(event) {
            const tooltip = this.querySelector('.tag-tooltip');
            if (tooltip && tooltip.style.display === 'block') {
                positionTooltip(tooltip, event);
            }
        });
        
        cell.addEventListener('mouseleave', function() {
            const tooltip = this.querySelector('.tag-tooltip');
            if (tooltip) {
                tooltip.style.display = 'none';
            }
        });
    });
    
    // Funktion zur dynamischen Tooltip-Positionierung
    function positionTooltip(tooltip, event) {
        const tooltipRect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let left = event.clientX + 15; // 15px Abstand zur Maus
        let top = event.clientY + 15;
        
        // Prüfe ob Tooltip rechts aus dem Viewport rausgeht
        if (left + tooltipRect.width > viewportWidth) {
            left = event.clientX - tooltipRect.width - 15;
        }
        
        // Prüfe ob Tooltip unten aus dem Viewport rausgeht
        if (top + tooltipRect.height > viewportHeight) {
            top = event.clientY - tooltipRect.height - 15;
        }
        
        // Stelle sicher, dass Tooltip nicht außerhalb des Viewports ist
        left = Math.max(10, Math.min(left, viewportWidth - tooltipRect.width - 10));
        top = Math.max(10, Math.min(top, viewportHeight - tooltipRect.height - 10));
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }
});

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

    // Tooltip-Funktionalität für Tag-Zellen
    const tagCells = document.querySelectorAll('.tag-cell');
    tagCells.forEach(function(cell) {
        cell.addEventListener('mouseenter', function() {
            const tooltip = this.querySelector('.tag-tooltip');
            if (tooltip) {
                tooltip.style.display = 'block';
            }
        });
        
        cell.addEventListener('mouseleave', function() {
            const tooltip = this.querySelector('.tag-tooltip');
            if (tooltip) {
                tooltip.style.display = 'none';
            }
        });
    });
});

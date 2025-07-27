# mp3-tagger-web
mp3-tagger-web

*Funktionsbeschreibung*
Zuerst wird das Quellverzeichnis ausgewwählt. Entwder das Verzeichnis wird manuell eingegeben oder per Explorer Auswahl ausgewählt.
Die App geht je Verzeichnis vor und scannt die MP3 Dateien und zeigt im ersten Schritt die Ergebnisse je verzeichnis an.
Die Ergebnisse können einzeln, je verzeichnis oder alle zusammen für die Weiterverarbeitung markiert werden. Die angezeigten Daten sind je Verzeichnis sortiert. Das aktuelle Verzeichnis steht über den Daten
Die gefundenen id3 Datem werden zeilenweise je mp3 Datei angezeigt.
Forlgende Daten werden angezeigt: Dateiname, Track Nummer, Artist, Titel, Album, sowie genre. Sollte es mehr ale einen Eintrag für das genre geben, wird das hauptgenre angezeigt und weitere genres summarisch (in einer klappe) bennannt.
Weiterhin wird angezeigt ob ein Cover in der MP3 gespeicht ist und in welchem Format 
Folgende Werte sind für die Coveranzeige möglich: 
- I<px size> (Intern mit Auflösung)
- E<px size> (Ein Logo liegt im Verzeichnis vor, ist aber nicht im mp3)
- Nein - Kein Logo vorhanden
- B <px size> Sowohl als exteren Logo Datei als auch im mp3 gespeichert. px size bezieht sich auf das Interne Logo
Alle weiterführenden Daten, die als id3 vorhanden sind sollen beim hoover über die entsprechende Datei sichtbar werden
Jede mp3 wird mit einem Play button ausgestattet, der unkompliziert ein Vorhören des jeweiligen Titels ermöglicht
Auf dieser Seite können die Eigenschaften Artist, Album und Titel, Tracknummer manuell überschrieben werden

**Sonderfall MP3 Dateien ohne id3 Informationen**
Sollte die mp3 Datei keine id3 informationen enthalten, wird versucht aufgrund des Verzeichnisnamens und des Dateinamens versucht relevante Information wie Titel, Tracknummer, Interpret zu ermitteln
Sofern Daten ermittelt werden können, werden diese dargestellt, werden aber optisch durch eine beige hintergrundfarbe hervorgehoben. Diese Daten können entweder so übernommen werden, oder sollten die ermittelten Informationen nicht korrekt sein, entweder überschrieben werden (Artist, Album und Titel, Tracknummer). Zusätzlich steht bei diesen Daten ein weiterer Button zur Verfügung, der über die vorhandenen Erkennungsmöglichkeiten (shaazam, acoustid, etc.) versucht die Datne zu ermittlen und darzustellen





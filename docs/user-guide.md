# RAG Dokumenten-KI: Benutzerhandbuch

Dieses Handbuch erklärt die Verwendung des RAG-basierten Dokumentabfragesystems.

## Einleitung

Das RAG Dokumenten-KI-System ermöglicht:

1. Das Hochladen von PDF- und CSV-Dokumenten
2. Die automatische Verarbeitung und Vektorisierung des Inhalts
3. Die Abfrage der Dokumente in natürlicher Sprache
4. Die Generierung von Antworten mit Quellenangaben

## Zugriffsvoraussetzungen

Benötigt wird lediglich ein moderner Webbrowser und die URL des Systems, die nach der Bereitstellung vom Administrator zur Verfügung gestellt wird.

## 1. Dokumente hochladen

1. Öffnen Sie die Web-Anwendung in Ihrem Browser.
2. Klicken Sie auf der Startseite auf die Schaltfläche "Zum Upload".
3. Im Upload-Bereich haben Sie zwei Möglichkeiten:
   - Klicken Sie auf die Upload-Zone und wählen Sie eine Datei aus dem Datei-Dialog.
   - Ziehen Sie eine Datei direkt per Drag & Drop in die Upload-Zone.
4. Wählen Sie eine PDF- oder CSV-Datei von Ihrem Gerät aus.
   - **Unterstützte Dateitypen:** PDF (.pdf), CSV (.csv), Text (.txt)
   - **Maximale Dateigröße:** 20 MB
5. Nachdem eine Datei ausgewählt wurde, erscheinen der Dateiname und die Größe in der Upload-Zone.
6. Klicken Sie auf die "Hochladen"-Schaltfläche, um den Upload zu starten.
7. Während des Uploads wird ein Ladeindikator angezeigt.
8. Nach erfolgreichem Upload erscheint eine Bestätigungsmeldung mit grünem Hintergrund.

**Hinweise:**

- Nach dem Hochladen startet automatisch die Verarbeitung des Dokuments im Hintergrund.
- Die Verarbeitungszeit hängt von der Dokumentgröße und -komplexität ab (typischerweise einige Sekunden bis Minuten).
- Eine Datei ist erst abfragbar, wenn die Verarbeitung abgeschlossen ist.

## 2. Dokumente abfragen

1. Klicken Sie auf der Startseite auf die Schaltfläche "Zur Abfrage" oder in der Navigation auf "Dokumente abfragen".
2. Im Abfragebereich geben Sie Ihre Frage in das Textfeld ein.
   - Formulieren Sie Ihre Frage möglichst klar und präzise.
   - Beispiele für gute Fragen:
     - "Was sind die wichtigsten Erkenntnisse aus dem Q3-Bericht?"
     - "Wie hoch waren die Verkaufszahlen für Produkt X im Jahr 2023?"
     - "Welche Risikofaktoren werden in der Analyse genannt?"
3. Klicken Sie auf "Suchen", um die Abfrage zu starten.
4. Während der Verarbeitung wird ein Ladeindikator angezeigt.
5. Das System sucht nach relevanten Informationen in den hochgeladenen Dokumenten und generiert eine Antwort.

## 3. Ergebnisse verstehen

Nach erfolgreicher Abfrage zeigt das System zwei Hauptbereiche an:

### Antwortbereich

Dieser Bereich enthält die generierte Antwort auf Ihre Frage. Die Antwort:

- Basiert ausschließlich auf den Informationen in den hochgeladenen Dokumenten.
- Zitiert die entsprechenden Quellen für die bereitgestellten Informationen.
- Kann mit "Keine relevanten Informationen gefunden" antworten, wenn die Frage nicht anhand der verfügbaren Dokumente beantwortet werden kann.

### Quellenbereich

Dieser Bereich listet die Dokumente und Abschnitte auf, die für die Antwort verwendet wurden:

- Jede Quelle zeigt den Dokumentnamen und ggf. die Seitennummer (bei PDFs).
- Klicken Sie auf "Textausschnitt anzeigen", um den genauen Text zu sehen, der als Quelle verwendet wurde.

## Tipps für effektive Abfragen

- **Spezifische Fragen stellen:** Je spezifischer Ihre Frage ist, desto genauer wird die Antwort sein.
- **Kontext hinzufügen:** Bei Bedarf können Sie zusätzlichen Kontext angeben (z.B. "In Bezug auf das Q3-Dokument...").
- **Mehrteilige Fragen vermeiden:** Stellen Sie lieber mehrere einzelne Fragen als eine komplexe Frage mit vielen Teilaspekten.
- **Bei unzureichenden Antworten:** Formulieren Sie Ihre Frage neu oder spezifizieren Sie sie weiter.

## Häufige Fragen

**F: Wie lange werden meine Dokumente gespeichert?**
A: Die Speicherdauer hängt von der Konfiguration des Systems durch den Administrator ab. In der Standardeinstellung werden Dokumente dauerhaft gespeichert, bis sie manuell gelöscht werden.

**F: Sind meine Dokumente sicher?**
A: Das System verwendet sichere Google Cloud-Dienste zur Speicherung und Verarbeitung Ihrer Dokumente. Die genauen Sicherheitsmaßnahmen hängen von der Konfiguration des Administrators ab.

**F: Warum erhalte ich keine Antwort auf meine Frage?**
A: Mögliche Gründe:
- Die relevanten Dokumente wurden noch nicht hochgeladen oder verarbeitet.
- Die Informationen sind nicht in den hochgeladenen Dokumenten enthalten.
- Die Frage ist zu vage oder außerhalb des Kontexts der vorhandenen Dokumente.

**F: Kann ich meine hochgeladenen Dokumente wieder löschen?**
A: Die grundlegende Version des Systems bietet keine direkte Funktion zum Löschen von Dokumenten durch Benutzer. Wenden Sie sich an den Administrator, wenn Sie Dokumente entfernen möchten.

## Fehlerbehebung

**Problem: Upload-Fehler**
Lösung: Überprüfen Sie:
- Dateityp (nur PDF, CSV, TXT unterstützt)
- Dateigröße (max. 20 MB)
- Netzwerkverbindung
- Versuchen Sie es erneut oder mit einer anderen Datei

**Problem: Lange Verarbeitungszeit**
Lösung:
- Größere Dokumente benötigen mehr Zeit zur Verarbeitung.
- Bei sehr langen Dokumenten kann die Verarbeitung bis zu mehreren Minuten dauern.
- Bei anhaltenden Problemen kontaktieren Sie den Administrator, der die Verarbeitungslogs prüfen kann.

**Problem: Unerwartete oder falsche Antworten**
Lösung:
- Überprüfen Sie die angegebenen Quellen auf Genauigkeit.
- Formulieren Sie Ihre Frage neu, um spezifischere Ergebnisse zu erhalten.
- Bei falschen oder irreführenden Informationen: Melden Sie dies dem Administrator.

## Support

Bei technischen Problemen oder Fragen wenden Sie sich bitte an Ihren Systemadministrator oder IT-Support.
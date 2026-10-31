# Pilotfall 001-2 (studentische Folgeerhebung)

Fachdokumentation zum ersten Datenpaket des Netzwerkmoduls. Enthält **keine Forschungsdaten und keine
personenbezogenen Einzelheiten**; ein Paket ist auch ohne Namen vertrauliches Forschungsmaterial (Wohnort,
Geburtsland und Beziehungsattribute können reidentifizieren) und liegt außerhalb des Repositorys.
Technik: [`../architecture/network-module.md`](../architecture/network-module.md).

## 1. Was der Fall ist – und was nicht

| Frage | Stand |
|---|---|
| Kennung | `001-2` ist die **historische Quellkennung** der Folgeerhebung, keine kanonische Fall-ID. Es ist keine Fall-ID registriert (kein Register); es wurde keine zugeordnet. |
| Verknüpfung | Die Folgeerhebung soll später mit der früheren Erhebung desselben Falls verknüpft werden. Das Paket belegt diesen Zusammenhang nicht; die Verknüpfung ist eine Registeraufgabe. |
| Herkunft (Lehrkontext) | studentische Folgeerhebung (Erhebungsart laut Paket: „network follow-up / student collection“), Sitzung vom 2026-09-25. Kohorte, Lehrveranstaltung, Erhebende (Pseudonym) und Instrument-Version sind **nicht belegt**; die formale Provenienz entsteht mit der Registrierung. Die studentische Herkunft bleibt auch nach professioneller Nachbearbeitung Teil der Provenienz ([`data-contract.md`](../architecture/data-contract.md) §3). |
| Datenherkunft | manuell aus Fotografien von vier ausgefüllten Erhebungsbögen und einer handgezeichneten Netzwerkkarte übertragen; Originalfotos nicht im Paket |
| Datenqualität | `UNREVIEWED`: **nicht** gegen die Originaldokumente geprüft. Die Datenlieferung ist ein manuell extrahierter Entwurf. |
| Freigabe | `NOT_DECIDED`; Erhaltung `NOT_PRESERVED`, Backup `NO_COPY` (kein `PRIMARY`, kein `BACKUP`) |

Diese vier Dimensionen – **Lehrkontext, Herkunft der Datenerhebung, Datenqualität, wissenschaftliche Freigabe** –
sind getrennt und folgen nicht auseinander. Eine technisch fehlerfreie Validierung ändert keine davon.

## 2. Wie die Alter-Alter-Beziehungen erhoben wurden

**Klarstellung der Projektleitung vom 2026-10-12** (sie berichtigt eine frühere Lesart dieser Dokumentation): Der
Explorator hat die Beziehungen zwischen den einzelnen Netzwerkpersonen **im Interview erfragt**. Die anschließend in
die Netzwerkkarte eingezeichneten Gruppenumrandungen fassen diese erhobenen Beziehungen **grafisch zusammen**. Alle
Personen innerhalb derselben bestätigten Gruppe kennen sich gegenseitig.

Daraus folgt die Unterscheidung zwischen

- **Erhebungsmethode:** Beziehungen einzeln erfragt;
- **Dokumentationsform:** Gruppenumrandungen der Netzwerkkarte (die Gruppenzugehörigkeit steht nicht im Tabellenblatt);
- **Paarabdeckung:** ob *jedes* der 231 möglichen Kontaktpaare erfasst wurde.

Die Cliquenregel („alle in einer Umrandung kennen sich“) ist deshalb für die sechs bestätigten Gruppen zulässig; die **41**
daraus folgenden ungerichteten Beziehungen (Überlappungen einfach gezählt) sind durch die Erhebung gedeckt, nicht durch
eine unbelegte Annahme.

**Was die vorliegenden Informationen nicht belegen:** dass jedes der 231 Paare erfragt wurde. Weder das Paket noch die
Klarstellung sagen, dass für Paare außerhalb der Gruppen eine Verneinung erhoben wurde. Deshalb bleiben die übrigen **190** Paare
**unbekannt** – sie gelten nicht als „kennen sich nicht“ –, und es werden keine Dichte-, Kohäsions-, Segregations- oder
Zentralitätsmaße berechnet. Sobald Explorator oder Projektleitung bestätigen, dass alle Paare erfasst wurden, kann dies in der
Kuratierung festgehalten werden (`pair_coverage: complete`); dann gelten fehlende Paare als verneint, und das Modul berechnet
Strukturmaße – als explorative Beschreibung eines Einzelfalls, ohne Verallgemeinerung. Keine bisher belegte Beziehung entfällt in
irgendeinem Fall.

Die Klarstellung steht in einer eigenen Kuratierungsdatei in `INTAKE` (mit Hash im Run-Record); die Originaldateien der Lieferung
sind unverändert.

## 3. Umfang der Lieferung

22 Kontakte; sechs bestätigte Kontaktgruppen (Paketversion 1.1); 41 ungerichtete Beziehungen. Die Kontakte stammen von zwei
Erhebungsblättern; auf dem zweiten Blatt wurde die lokale Nummerierung irrtümlich neu begonnen und im Paket auf `A16`–`A22`
abgebildet. Die ursprünglichen Nummern und das Blatt bleiben als Provenienz erhalten. Die sechs Gruppen überlappen: eine kleine
Gruppe liegt vollständig im Durchschnitt zweier größerer; die Überlappung zählt keine Beziehung doppelt.

Die erste Lieferung (Paketversion 1.0) enthielt vier bestätigte und zwei unklare Gruppen (22 Beziehungen). Mit Version 1.1 wurden die
beiden unklaren Gruppen am 2026-10-12 von der Projektseite ausdrücklich bestätigt (`source_clarifications.csv`); die Lieferung 1.0
wurde auf Anweisung der Projektleitung ersetzt und gelöscht. Die Bestätigung beruht auf einer Angabe der Projektseite, **nicht** auf
einer unabhängigen Prüfung der Quelle; der Prüfbericht vermerkt das bei jeder betroffenen Gruppe.

## 4. Prüfhinweise (Stand der Kuratierung)

Die Prüfhinweise des Pakets sind in vier Kategorien eingeordnet (Kategorien: [`network-module.md`](../architecture/network-module.md) §5.1).
Jede Entscheidung trägt ihren Urheber (Projektleitung oder Vorschlag des Agenten).

| Gegenstand | Kategorie | Behandlung |
|---|---|---|
| abweichende Namensschreibung eines Kontakts zwischen Tabelle und Karte | geklärt | maßgeblich ist die Kontakt-ID; kein Datenfehler (Projektleitung) |
| Geburtsland mit zwei genannten Ländern (ein Kontakt) | dokumentierte Mehrdeutigkeit | Rohwert erhalten; Status „mehrdeutig“; weder ein Land gewählt noch zwei gezählt noch als fehlend behandelt (Projektleitung) |
| Wohnort „Nähe Marburg“ (ein Kontakt) | akzeptierte Unschärfe | als „Region Marburg“ geführt, Deutschland, nicht die Stadt; kein konkreter Wohnort erfunden (Projektleitung) |
| Regel „nur der Tabellenwert 1–5 gilt“ | geklärt | Kartenposition und Legende werden nicht verwendet (Projektleitung) |
| Gruppenzugehörigkeit aus der Karte | geklärt | Dokumentationsform der erhobenen Beziehungen, kein erschlossener Befund (Projektleitung) |
| Datenschutzhinweis (keine Namen im Paket) | geklärt | kein Datenproblem (Vorschlag) |
| Normalisierung einer Standardabkürzung eines Ortsnamens | geklärt | im Paket vermerkt (Vorschlag, zu bestätigen) |
| handschriftliche Ergänzungen zu Sprachmodus und Sprachwahl bei drei Kontakten; ein nicht übertragener Freitext | dokumentierte Mehrdeutigkeit | Codes bleiben wie erhoben; ohne Originalbogen nichts ergänzt (Vorschlag, zu bestätigen) |
| möglicherweise zusätzliche Funktionscodes bei einem Kontakt | **offen** | nur am Originalbogen entscheidbar; nicht übernommen |
| Paarabdeckung (werden alle 231 Paare erfragt?) | **offen** | siehe §2 |
| Fall-ID, Provenienz, Quellenprüfung | **offen** | Registeraufgaben |

Sprachmodus 6 bei zwei Kontakten ist ohne Erläuterung im Paket; er bleibt als erhobener Wert bestehen und wird nicht umcodiert.
Eine fehlende Erläuterung ist kein Grund, den Code zu ändern. Die handschriftlichen Originalbögen lagen der Verarbeitung nicht vor;
ob sich offene Fragen dort klären lassen, ist eine Aufgabe der Quellenprüfung.

## 5. Methodische Einschränkungen

1. **Paarabdeckung nicht belegt** (§2): belegt sind die 41 bestätigten Beziehungen; die übrigen Paare sind unbekannt.
2. **Nähe = Tabellenwert 1–5.** Position auf der Karte und die abweichende (vierstufige) Kartenlegende bleiben außen vor; es wird nicht
   umgerechnet.
3. **Mehrfachcodierungen.** Handschriftliche Bereiche sind im Paket in Einzelcodes aufgelöst; Mehrfachsprachigkeit bleibt
   Mehrfachsprachigkeit, es wird keine Hauptsprache abgeleitet; Sprachmodus 5 und 6 bleiben eigene Werte.
4. **Ungefähre und mehrdeutige Angaben** (ein Wohnort, ein Geburtsland) bleiben erhalten und sind als solche ausgewiesen, nicht präzisiert.
   Die Einordnung „Marburg“ gilt nur bei exakt benanntem Ort.
5. **Das Netzwerk eines einzelnen Falls** erlaubt keine Schlüsse auf Gruppen oder Populationen; auch bei bestätigter Paarabdeckung wären
   Strukturmaße explorativ und beschreibend.
6. **Darstellung:** die Netzwerkabbildung ist ein kraftbasiertes Layout. Die Position eines Kontakts ergibt sich aus seinen
   Beziehungen; sie ist keine räumliche oder soziale Nähe zu Ego, und der Abstand getrennter Teilnetze hat keine Bedeutung.

## 6. Nächste fachliche Schritte

Bestätigung der Paarabdeckung (Explorator/Projektleitung); Quellenprüfung der Daten gegen die Originalbögen, insbesondere die
Funktionscodes eines Kontakts und die handschriftlichen Ergänzungen; Bestätigung der als Vorschlag gekennzeichneten
Kuratierungseinträge; Registrierung des Falls und Verknüpfung mit der früheren Erhebung (Fall-ID, Provenienz).

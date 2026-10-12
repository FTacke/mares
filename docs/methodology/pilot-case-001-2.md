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

## 2. Umfang der Lieferung

22 Kontakte; sechs bestätigte Kontaktgruppen (Paketversion 1.1); 41 ungerichtete Beziehungen, abgeleitet aus
den Gruppen. Die Kontakte stammen von zwei Erhebungsblättern; auf dem zweiten Blatt wurde die lokale
Nummerierung irrtümlich neu begonnen und im Paket auf `A16`–`A22` abgebildet. Die ursprünglichen Nummern und das
Blatt bleiben als Provenienz erhalten.

Die erste Lieferung (Paketversion 1.0) enthielt vier bestätigte und zwei unklare Gruppen (22 Beziehungen). Mit
Version 1.1 wurden die beiden unklaren Gruppen am 2026-10-12 von der Projektseite ausdrücklich bestätigt
(`source_clarifications.csv`); die Lieferung 1.0 wurde auf Anweisung der Projektleitung ersetzt und gelöscht.
Die Bestätigung beruht auf einer Angabe der Projektseite, **nicht** auf einer unabhängigen Prüfung der Quelle; der
Prüfbericht vermerkt das bei jeder betroffenen Gruppe.

## 3. Methodische Einschränkungen

1. **Alter-Alter-Erhebung unvollständig.** Belegt sind nur Beziehungen aus bestätigten Gruppenumrandungen nach der
   Cliquenregel („alle innerhalb derselben Umrandung kennen sich“). Alle anderen Paare sind **unbekannt**, nicht
   „kennen sich nicht“. Dichte, Kohäsion und Segregation werden deshalb nicht berechnet.
2. **Gruppen ohne Tabellenbeleg.** Die Gruppenzugehörigkeit steht nicht im Erhebungsblatt, sondern ist aus der
   Kartenskizze erschlossen.
3. **Nähe = Tabellenwert 1–5.** Position auf der Karte und die abweichende (vierstufige) Kartenlegende bleiben
   außen vor; es wird nicht umgerechnet.
4. **Mehrfachcodierungen.** Handschriftliche Bereiche sind im Paket in Einzelcodes aufgelöst; Mehrfachsprachigkeit bleibt
   Mehrfachsprachigkeit, es wird keine Hauptsprache abgeleitet.
5. **Ungefähre und mehrdeutige Angaben** (ein Wohnort, eine Herkunftsangabe) bleiben, wie sie sind; sie sind
   markiert und nicht präzisiert. Die Einordnung „Marburg“ gilt nur bei exakt benanntem Ort.
6. **Bekannte Lesartenfragen** stehen im Prüfbericht jedes Laufs unter „Offene Forschungsfragen“: u. a. mögliche
   zusätzliche Funktionscodes bei einem Kontakt, eine abweichende Personenbeschriftung zwischen Tabelle und Karte, eine
   mehrdeutige Herkunftsangabe, Sprachmodus-Ergänzungen von Hand, ein nicht übertragener Freitext. Sie werden
   dokumentiert und als Reviewfrage geführt, nicht von der Software entschieden.
7. Das Netzwerk eines einzelnen Falls erlaubt **keine** Schlüsse auf Gruppen oder Populationen.

## 4. Nächste fachliche Schritte

Quellenprüfung der Daten gegen die Originalbögen (Datenqualität); Registrierung des Falls und Verknüpfung mit der
früheren Erhebung (Fall-ID, Provenienz); Entscheidung über die offenen Reviewfragen; Klärung, ob eine explizite
Alter-Alter-Erhebung nachgeholt werden soll, damit strukturelle Kennzahlen zulässig werden.

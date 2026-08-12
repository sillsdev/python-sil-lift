# Überprüfen

Die Validierung erfolgt immer explizit – beim Laden und Speichern findet niemals eine implizite Validierung statt.

```python
import sil_lift

# Vollständig: ein „lazy“ Stream von Problemen (Schema + semantische Ebenen).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # Fehler [dangling-ref] dictionary.lift:88 (Eintrag apu): ref 'nope' passt zu ...

# Fail-fast: Löst bei dem ersten Problem auf Fehler-Ebene einen LiftValidationError aus.
sil_lift.validate_file("dictionary.lift")

# In-Memory-Zustand (wird zunächst serialisiert – ein dokumentierter Mehraufwand bei großen Lexika):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Jedes `Problem` enthält einen `Level` (`"error"`/`"warning"`), einen festen `Code`, eine `Meldung` sowie folgende Angaben: `Datei`, `Eintrags-ID`, `GUID`, `Zeile`.

## Die Schichten

1. **RELAX NG** gemäß der LIFT 0.13-Grammatik (aus „lift-standard“ übernommen – eine byteweise identische Kopie, die in dieses Paket integriert wurde).
2. **Ranges-Schema** – in diesem Projekt `lift-ranges-0.13.rng` – für jeden erfassten `.lift-ranges`-Begleiter.
3. **Semantische Prüfungen**, die die Grammatik nicht ausdrücken kann: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`.

## Praktische FieldWorks (FLEx)-Ergebnisse

FieldWorks schreibt systematisch bestimmte Inhalte, die von strengen Validierungstools abgelehnt werden. Hier sind die Richtlinien von sil-lift, damit echte Lexika sinnvoll validiert werden können:

- `file://C:/...`-href-Attribute (ungültige URIs) werden als **Warnungen** (`uri-not-rfc`) gemeldet, nicht als Schemafehler – der C#-Validator hat sie nie abgelehnt.
- Rechtmäßig verschachtelte Kinder (z. B. in gewisser Weise `field, note, field, note`) werden **nicht** markiert, wodurch ein Fehlalarm in libxml2 umgangen wird.
- Bereichswerte werden unter der Unicode-NFC-Normalisierung verglichen – FLEx schreibt die `.lift`-Daten in NFC, die `.lift-ranges`-Daten jedoch in NFD innerhalb desselben Exports.
- Die `trait`/`field`-Erweiterungen von FLEx innerhalb von `range-element` **werden** gemeldet (Schemafehler in Bezug auf das Ranges-Schema): Es handelt sich dabei um echte Abweichungen von der Spezifikation.

# Ejemplo práctico: cómo crear una exportación LIFT desde cero

Si estás exportando los datos de otra aplicación en formato LIFT —la tarea que subyace a [La generación de LIFT conforme a las normas](lift-export-interop.md)—, `sil-lift` puede construir el documento objeto a objeto y serializarlo, en lugar de generar el XML manualmente. Aquí se explica paso a paso cómo funciona un script que crea una entrada con los elementos que contiene un diccionario real (varios sistemas de escritura, una pronunciación, un significado con un ejemplo, una ilustración, una característica de dominio semántico y un campo específico de la aplicación), escribe los vocabularios controlados en un archivo complementario `.lift-ranges`, los valida y los guarda.

## El guión

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Una entrada, creada a partir del modelo de origen.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Hablante: Ana"  # La convención de etiquetas de hablantes de The Combine
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "ave doméstica criada por sus huevos y su carne"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Una gallina"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # un campo adicional específico de la aplicación
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Los vocabularios controlados a los que hace referencia la entrada, en un archivo .lift-ranges complementario.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Valida lo que escribiría save(), antes de guardar en el disco.
problems = list(lex.iter_problems())
print(f"validación: {len(problems)} problema(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## Qué produce

`validación: 0 problema(s)`, y a continuación el `.lift` y su equivalente, uno al lado del otro:

```
=== birds.lift ===
<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="my-exporter">
<header>
  <ranges>
    <range id="grammatical-info" href="birds.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="birds.lift-ranges"/>
  </ranges>
</header>
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d">
  <lexical-unit>
    <form lang="seh">
      <text>nkhuku</text>
    </form>
    <form lang="pt">
      <text>gallina</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Hablante: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>gallina</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>ave doméstica criada por sus huevos y su carne</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>Quiero un pollo.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>Una gallina</text>
        </form>
      </label>
    </illustration>
    <trait name="semantic-domain-ddp4" value="1.6.1.2"/>
    <field type="scientific-name">
      <form lang="en">
        <text>Gallus gallus domesticus</text>
      </form>
    </field>
  </sense>
</entry>
</lift>
=== aves.gamas de peso ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>sustantivo</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Ave</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Notas sobre la API

- Campos multitexto (`lexical_unit`, `definition`, una etiqueta de `Form`/`URLRef`, el contenido de un `Field`, etc.) Selecciona una cadena por sistema de escritura a través de la interfaz de mapeo: `entry.lexical_unit["seh"] = "nkhuku"` añade un `<form lang="seh">`. Un modelo de origen que indexa las cadenas por código de idioma se corresponde directamente con esto.
- `RangesFile.add_range()` / `Range.add_element()` crean los vocabularios controlados, y `Lexicon.add_ranges_file(ranges, href=...)` adjunta el archivo complementario y añade las referencias de encabezado `<range href>`, de modo que las entradas `<grammatical-info value="Noun">` y `<trait name="semantic-domain-ddp4" value="1.6.1.2">` se resuelven en función de los rangos que hayas definido.
- Un `URLRef` es un atributo `href` junto con un texto múltiple opcional (leyenda o etiqueta), que se utiliza tanto para `<media>` (audio) como para `<illustration>` (fotos). La pronunciación aquí sigue la convención de The Combine, que consiste en una forma «en» que se lee « <name> ».
- Datos específicos de la aplicación que no contengan desplazamientos de ida a casa nativos de LIFT como «<field> » (o «<trait> »): FieldWorks los interpreta como campos personalizados y The Combine los conserva.
- Asigna a cada entrada un `guid` real y estable (por ejemplo, generado con `uuid.uuid4()`, que se reutilice en todas las exportaciones): así, si se vuelve a importar más adelante, la entrada se actualizará in situ en lugar de duplicarse. El comando `sil-lift validate --require-ids` garantiza el cumplimiento de esta norma.
- `lex.iter_problems()` comprueba la validez del documento almacenado en memoria (lo que escribiría `save()`) antes de que nada se guarde en el disco; aquí está en perfecto estado. Dado que el léxico aún no tiene ninguna carpeta, se omiten las comprobaciones de «media-presence» y «companion-href»: ejecuta [`sil-lift validate`](cli.md) sobre el resultado guardado (o con `--no-check-media`) una vez que los archivos de audio y las fotos estén en su sitio.

## Embalaje

`lex.save("export/birds.lift")` guarda la estructura de la carpeta (los archivos `.lift` y `.lift-ranges` uno al lado del otro). Para generar un único paquete comprimido que FieldWorks y The Combine puedan importar directamente, utiliza en su lugar `lex.save_zip("birds.zip")`; consulta [Cómo generar archivos LIFT conformes](lift-export-interop.md).

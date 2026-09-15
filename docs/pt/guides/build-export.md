# Exemplo prático: criar uma exportação LIFT a partir do zero

Se estiver a exportar dados de outra aplicação no formato LIFT — a tarefa subjacente a [Produção de LIFT em conformidade](lift-export-interop.md) — o `sil-lift` pode construir o documento objeto a objeto e serializá-lo, em vez de gerar XML manualmente. Este guia explica passo a passo um script que cria uma entrada com os elementos que um dicionário real possui (vários sistemas de escrita, uma pronúncia, um significado com um exemplo, uma ilustração, uma característica do domínio semântico e um campo específico da aplicação), grava os vocabulários controlados num ficheiro complementar `.lift-ranges`, valida e guarda.

## O guião

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Uma entrada, criada a partir do modelo de origem.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # A convenção de rotulagem de falantes do Combine
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Substantivo")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "uma ave doméstica criada pelos seus ovos e carne"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Uma galinha"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # um campo extra específico da aplicação
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Os vocabulários controlados a que a entrada se refere, num ficheiro .lift-ranges.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Validar o que o save() escreveria, antes de gravar no disco.
problems = list(lex.iter_problems())
print(f"validação: {len(problems)} problema(s)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## O que produz

`validação: 0 problema(s)`, e, em seguida, o `.lift` e o seu equivalente lado a lado:

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
      <text>galinha</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Speaker: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>chicken</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>a domestic fowl kept for its eggs and meat</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>I want a chicken.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>A hen</text>
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
=== birds.lift-ranges ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>noun</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Bird</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Notas sobre a API

- Campos multitexto (`lexical_unit`, `definition`, um rótulo de `Form`/`URLRef`, o conteúdo de um `Field`, ...) selecione uma sequência por sistema de escrita através da interface de mapeamento: `entry.lexical_unit["seh"] = "nkhuku"` adiciona um `<form lang="seh">`. Um modelo de origem que indexa cadeias de caracteres pelo código do idioma corresponde diretamente a isto.
- `RangesFile.add_range()` / `Range.add_element()` criam os vocabulários controlados, e `Lexicon.add_ranges_file(ranges, href=...)` associa o vocabulário complementar e adiciona as referências de cabeçalho `<range href>` — para que os campos `<grammatical-info value="Noun">` e `<trait name="semantic-domain-ddp4" value="1.6.1.2">` da entrada sejam resolvidos de acordo com os intervalos que definiu.
- Um `URLRef` é um href acompanhado de um texto múltiplo opcional (legenda/rótulo) — utilizado tanto para `<media>` (áudio) como para `<illustration>` (fotografias). A pronúncia aqui segue a convenção do The Combine, que prevê uma forma «en» que se lê «Orador: <name> ».
- Dados específicos da aplicação que não incluam viagens de regresso a casa nativas do LIFT, como «<field> » (ou «<trait> »): o FieldWorks interpreta-os como campos personalizados e o The Combine preserva-os.
- Atribua a cada entrada um `guid` válido e estável (por exemplo, gerado por `uuid.uuid4()`, reutilizado em todas as exportações) — uma reimportação posterior atualiza a entrada no local, em vez de a duplicar. O comando `sil-lift validate --require-ids` garante que isso seja cumprido.
- A função `lex.iter_problems()` valida o documento na memória (o que a função `save()` iria gravar) antes de qualquer coisa ser gravada no disco; neste caso, está correto. Como o léxico ainda não tem nenhuma pasta, as verificações de «media-presence» e «companion-href» são ignoradas — execute [`sil-lift validate`](cli.md) na saída guardada (ou com `--no-check-media`) assim que os ficheiros de áudio e de fotografias estiverem no local.

## Embalagem

`lex.save("export/birds.lift")` grava a estrutura da pasta (ficheiros `.lift` e `.lift-ranges` lado a lado). Para gerar um único pacote compactado que o FieldWorks e o The Combine importem diretamente, utilize `lex.save_zip("birds.zip")` — consulte [Produção de LIFT em conformidade](lift-export-interop.md).

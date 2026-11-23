# Ler, editar, escrever

## A carregar

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Tudo o que o modelo não definir (elementos/atributos desconhecidos, comentários) é transportado sem perdas como resíduo LIFT no campo opaco `extra` de cada nó. Outras versões do LIFT provocam um `LiftParseError` indicando a versão.

## O modelo

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Um texto multilingue é um `Multitext`, que consiste num `Mapping` do código do idioma para `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` converte o texto em texto simples; os fragmentos mantêm a marcação para permitir a conversão de ida e volta.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

No LIFT, as glosas têm a forma de _formas_ (cada `<gloss>` contém a sua própria linguagem), pelo que um sentido tem `glosses: list[Form]`, além de funções auxiliares:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Recorra à função `all_senses()` sempre que uma questão diga respeito à entrada na sua totalidade: contar significados, recolher línguas, encontrar meios de comunicação. `entry.senses` fornece o nível superior, que é o que se pretende apenas quando o próprio aninhamento é relevante.

## Poupança

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

As entradas que não foram modificadas são gravadas de volta **identicamente, ao nível do byte**; um documento que não tenha sido modificado de todo é idêntico, ao nível do byte, desde o primeiro byte até ao último. Consulte [Garantias da Fidelity](../fidelity.md) para conhecer o contrato na íntegra.

### Marcações temporais

Os registos que modificou são publicados com uma nova `dateModified` (e uma `dateCreated`, caso não tivessem nenhuma), pelo que uma edição não é publicada com a data com que foi carregada. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Consulte [Carimbos de data/hora gerados](../fidelity.md#generated-timestamps) para conhecer o resto das regras.

### Skipping a save that changes nothing

Para ignorar um salvamento que não alteraria nada, proteja-o com `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

Retorna `False` apenas quando `save()` reproduzir os bytes de origem, abrangendo as entradas, o cabeçalho, o elemento raiz e todos os elementos `.lift-ranges` associados. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Pára na primeira diferença, pelo que, num léxico editado, o custo é praticamente nulo. Um léxico inalterado tem de ser serializado na íntegra para comprovar que não sofreu alterações, mas isso ainda assim custa menos do que o processo de gravação que é omitido.

Como compara o conteúdo e não o destino, certifique-se de que o arquivo é guardado no mesmo local. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

## Construir do zero

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Ordenação canónica

```python
lex.sort()      # entradas por (guid, id); intervalos/definições de campos por id/tag
lex.save()      # as entradas não alteradas mantêm os seus bytes exatos, na nova ordem

sil_lift.canonicalize("in.lift", "out.lift")   # totalmente resserializado, pronto para comparação de diferenças
```

Ver também: [Exemplo prático: edição em massa de glossários](bulk-edit-glosses.md).

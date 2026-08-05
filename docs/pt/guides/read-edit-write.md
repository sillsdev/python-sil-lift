# Ler, editar, escrever

## A carregar

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

A função `load()` aceita qualquer documento LIFT **0.13** bem formado — incluindo ficheiros reais que não estejam em conformidade com o esquema. Tudo o que o modelo não definir (elementos/atributos desconhecidos, comentários) é transportado sem perdas no compartimento opaco `extra` de cada nó. Outras versões do LIFT provocam um `LiftParseError` indicando a versão.

## O modelo

Cada elemento do LIFT é uma classe de dados tipada: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, e assim por diante. Um texto multilingue é um `Multitext`, que funciona como um mapeamento de um código de idioma para `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # as cadeias de caracteres simples são convertidas
"en" in entry.citation                  # False
```

O `Text` está estruturado — uma lista ordenada de fragmentos `str` e `Span` — porque `<text>` pode conter marcação aninhada `<span>`. `str(text)` converte o texto em texto simples; os fragmentos mantêm a marcação para permitir a conversão de ida e volta.

No LIFT, as glossas têm a forma de _Form_ (cada `<gloss>` contém a sua própria linguagem), pelo que um sentido tem `glosses: list[Form]`, além de uma função auxiliar:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Texto | None
entry.gloss_langs()                     # {"en", "id"}
```

## Poupança

```python
lex.save()                # voltar para o local de onde foi carregado
lex.save("elsewhere.lift")
```

As entradas que não foram modificadas são gravadas de volta **identicamente, ao nível do byte**; um documento que não tenha sido modificado de todo é idêntico, ao nível do byte, desde o primeiro byte até ao último. Consulte [Garantias da Fidelity](../fidelity.md) para conhecer o contrato na íntegra.

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

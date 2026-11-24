# Ler, editar, escrever

## A carregar

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

A função `load()` aceita qualquer documento LIFT **0.13** bem formado, incluindo ficheiros reais que não estejam em conformidade com o esquema. Tudo o que o modelo não definir (elementos/atributos desconhecidos, comentários) é transportado sem perdas como resíduo LIFT no campo opaco `extra` de cada nó. Outras versões do LIFT provocam um `LiftParseError` indicando a versão.

## O modelo

Cada elemento do LIFT é uma classe de dados tipada: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, e assim por diante.

### Texto multilingue

Um texto multilingue é um `Multitext`, que consiste num `Mapping` do código do idioma para `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # as cadeias de caracteres simples são convertidas
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

O `Texto` é estruturado (uma lista ordenada de fragmentos `str` e `Span`) porque `<text>` pode conter marcação aninhada `<span>`. `str(text)` converte o texto em texto simples; os fragmentos mantêm a marcação para permitir a conversão de ida e volta.

O mapeamento apresenta um valor por língua. Por baixo, `forms` contém todos os `<form>` pela ordem em que aparecem no ficheiro. Um documento válido segundo o esquema tem, no máximo, um formulário por idioma, mas, na prática, os ficheiros por vezes repetem um.

Como o mapeamento é indexado por idioma, a função `len()` conta os idiomas em vez dos formulários, e as visualizações `keys()`, `values()` e `items()` listam cada idioma uma única vez. Ambos os mutadores atuam também em toda a língua: `del entry.lexical_unit["en"]` remove todas as formas em inglês, e a atribuição a `"en"` deixa exatamente uma.

No caso de uma língua repetida, `entry.lexical_unit["en"]`, `get()`, `values()` e `items()` apresentam sempre a sua primeira forma, e [`validate`](validate.md#problem-codes) indica o erro `duplicate-form-lang` até que se atribua um valor a essa língua.

Não é possível criar, através do mapeamento, um formulário que não inclua qualquer atributo `lang`. É registado como «form-missing-lang» e é eliminado quando o seu nó é novamente serializado.

### Significados e glosas

No LIFT, as glosas têm a forma de _formas_ (cada `<gloss>` contém a sua própria linguagem), pelo que um sentido tem `glosses: list[Form]`, além de funções auxiliares:

```python
sense = entry.senses[0]       # apenas o nível superior
sense.gloss("en")             # Texto | None
entry.all_senses()            # todos os sentidos e sub-sentidos, por ordem de aparecimento no documento
entry.gloss_langs()           # {"en", "id"}, incluindo os sub-sentidos
```

Recorra à função `all_senses()` sempre que uma questão diga respeito à entrada na sua totalidade: contar significados, recolher línguas, encontrar meios de comunicação. `entry.senses` fornece o nível superior, que é o que se pretende apenas quando o próprio aninhamento é relevante.

## Poupança

```python
lex.save()                    # de volta ao local de onde foi carregado
lex.save("elsewhere.lift")
```

As entradas que não foram modificadas são gravadas de volta **identicamente, ao nível do byte**; um documento que não tenha sido modificado de todo é idêntico, ao nível do byte, desde o primeiro byte até ao último. Consulte [Garantias da Fidelity](../fidelity.md) para conhecer o contrato na íntegra.

### Marcações temporais

Os registos que modificou são publicados com uma nova `dateModified` (e uma `dateCreated`, caso não tivessem nenhuma), pelo que uma edição não é publicada com a data com que foi carregada. As ferramentas que realizam a fusão do LIFT determinam o que mudou nesse atributo. Existem dois argumentos que ajustam a estampagem:

- `lex.save(stamp=False)` grava as datas que o modelo contém e nada mais.
- `lex.save(when=...)` fixa o momento em vez de consultar o relógio.

Consulte [Carimbos de data/hora gerados](../fidelity.md#generated-timestamps) para conhecer o resto das regras.

### Ignorar um salvamento que não altera nada

Para ignorar um salvamento que não alteraria nada, proteja-o com `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

Retorna `False` apenas quando `save()` reproduzir os bytes de origem, abrangendo as entradas, o cabeçalho, o elemento raiz e todos os elementos `.lift-ranges` associados. Se não se efetuar a gravação, a data de modificação do ficheiro permanece inalterada e evita-se um diff espúrio.

O cheque é barato. Pára na primeira diferença, pelo que, num léxico editado, o custo é praticamente nulo. Um léxico inalterado tem de ser serializado na íntegra para comprovar que não sofreu alterações, mas isso ainda assim custa menos do que o processo de gravação que é omitido.

Como compara o conteúdo e não o destino, certifique-se de que o arquivo é guardado no mesmo local. `lex.save("elsewhere.lift")` grava o documento e os seus ficheiros associados no novo caminho, mesmo quando `changes()` é `False`; por isso, se se colocasse uma condição de verificação, essa cópia seria ignorada.

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

# Exemplo prático: edição em massa de glossários

Uma tarefa de manutenção comum: uniformizar a ortografia em todas as entradas em inglês de um léxico (britânica → americana, ou vice-versa) sem alterar qualquer outro aspeto do ficheiro. Este exemplo apresenta um script que carrega, edita, valida e guarda — demonstrando como a API de edição e a garantia de fidelidade funcionam em conjunto.

## O guião

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"interrompendo: {len(errors)} erro(s) de validação, nada guardado")

lex.save()
print(f"glossário(s) editado(s) {edited_glosses} em {len(changed)} entrada(s)")
```

Algumas coisas que vale a pena referir:

- `entry.all_senses()` devolve todos os sentidos _e sub-sentidos_, em ordem de profundidade, seguindo a ordem do documento.
  - `entry.senses` contém apenas o nível superior, pelo que uma edição em massa que percorresse esse elemento ignoraria silenciosamente qualquer glossário aninhado sob um sub-significado.
- `gloss.text` é um `Text`, não uma string simples: `str(gloss.text)` simplifica-o para efeitos de correspondência, e a substituição é gravada novamente com `sil_lift.Text([new])`, em vez de alterar a string no local.
- A função `lex.changed_entries()` indica quais as entradas que diferem do ficheiro tal como foi carregado. Uma vez que o resumo de uma entrada abrange toda a sua subárvore, uma alteração num sub-significado aninhado é registada na entrada que o contém, enquanto que a atribuição a um campo do valor que este já possuía não é registada.
- A função `changed_entries()` abrange apenas o conteúdo das entradas, pelo que se trata de uma contagem e não de uma proteção contra gravações. Para ignorar um processo de gravação que não alteraria nada, utilize `lex.changes()`; consulte [Gravação](read-edit-write.md#saving).
- A validação na memória (`lex.iter_problems()`) serializa primeiro o estado editado, para que este reflita corretamente a edição antes de qualquer coisa ser gravada no disco. A interrupção ao ocorrer qualquer `Problem` de nível `"error"` — os avisos são deixados para que quem chamou a função decida o que fazer — significa que uma edição incorreta nunca chega à função `save()`.
- A função `lex.save()` atribui uma nova data `dateModified` exatamente às entradas que este script alterou, preenchendo o campo `dateCreated` nos casos em que este estava em branco. Sem isso, um léxico reescrito por este script pareceria inalterado para o FieldWorks ou para a importação LIFT do The Combine, uma vez que ambos determinam o que atualizar a partir desse atributo — e apenas marca `<entry>`, independentemente da profundidade da edição: a entrada que contém a glossária do sub-significado editado, e não o próprio significado.

Os glosses não são a única coisa que vale a pena tratar desta forma. A mesma superfície de mapeamento `Multitext` aplica-se às definições e a todos os outros campos multilingues de uma entrada ou significado:

```python
sense.definition["en"] = "a cor de uma coisa"
```

## Executá-lo

Execute a pesquisa com um pequeno léxico que contenha uma entrada e uma subentrada cujos significados sejam ambos «cor»:

```
editou 2 glossários em 1 entrada(s)
```

## A recompensa pela fidelidade

A garantia aplica-se a cada _entrada_: uma entrada cujo modelo não tenha sido alterado é devolvida **identicamente em termos de bytes** à forma como foi lida, e apenas as entradas em que se interveio efetivamente são resserializadas. Na execução acima, foram editadas as anotações de uma entrada — todas as outras entradas do ficheiro mantiveram os seus bytes exatos. (Repare na granularidade: a edição de qualquer parte de uma entrada faz com que toda a entrada seja novamente serializada, incluindo os significados associados que não foram alterados.) A edição de uma definição num léxico com 50 000 entradas resulta, portanto, num ficheiro «diff» que afeta apenas uma entrada, e não num ficheiro reformatado. Consulte [Garantias da Fidelity](../fidelity.md) para conhecer o contrato na íntegra.

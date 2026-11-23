# Exemplo prático: edição em massa de glossários

Uma tarefa de manutenção comum: uniformizar a ortografia em todas as entradas em inglês de um léxico (britânica → americana, ou vice-versa) sem alterar qualquer outro aspeto do ficheiro. Este exemplo apresenta um script que carrega, edita, valida e guarda, mostrando como a API de edição e a garantia de fidelidade funcionam em conjunto.

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
- `lex.changed_entries()` apresenta as entradas cujo conteúdo difere do ficheiro tal como foi carregado. Qualquer alteração efetuada em qualquer parte de uma entrada, mesmo num sub-significado aninhado, faz com que essa entrada seja comunicada. Atribuir a um campo o valor que este já tinha não gera qualquer mensagem, uma vez que o conteúdo permanece inalterado.
- A função `changed_entries()` abrange apenas o conteúdo das entradas, pelo que se trata de uma contagem e não de uma proteção contra gravações. Para ignorar um processo de gravação que não alteraria nada, utilize `lex.changes()`; consulte [Gravação](read-edit-write.md#saving).
- A validação na memória (`lex.iter_problems()`) serializa primeiro o estado editado, para que este reflita corretamente a edição antes de qualquer coisa ser gravada no disco. Interromper a execução perante qualquer `Problem` de nível `"error"` (os avisos são deixados para que quem chamou a função decida o que fazer) significa que uma edição incorreta nunca chega à função `save()`.
- A função `lex.save()` atribui uma nova data `dateModified` exatamente às entradas que este script alterou, preenchendo o campo `dateCreated` nos casos em que este estava em branco.
  - Tanto o FieldWorks como a importação LIFT do The Combine determinam o que atualizar com base em `dateModified`; por isso, sem a data mais recente, considerariam as entradas editadas como inalteradas.
  - Apenas os elementos `<entry>` são marcados. Quando se edita uma nota explicativa de um sub-significado, a data é atribuída à entrada que a contém, e não ao próprio significado.

## Executá-lo

Execute a pesquisa com um pequeno léxico que contenha uma definição e uma definição de sub-significado que, ambas, indiquem «cor»:

```
editou 2 glossários em 1 entrada(s)
```

## A recompensa pela fidelidade

A garantia aplica-se a cada _entrada_: uma entrada cujo modelo não tenha sido alterado é devolvida **identicamente em termos de bytes** à forma como foi lida, e apenas as entradas em que se interveio efetivamente são resserializadas. Na execução acima, foram editadas as anotações de uma entrada; todas as outras entradas do ficheiro mantiveram os seus bytes exatos. A edição de uma definição num léxico com 50 000 entradas resulta, portanto, num ficheiro «diff» que afeta apenas uma entrada, e não num ficheiro reformatado.

Repare na granularidade: a edição de qualquer parte de uma entrada faz com que toda a entrada seja novamente serializada, incluindo os significados associados que não foram alterados. Consulte [Garantias da Fidelity](../fidelity.md) para conhecer o contrato na íntegra.

## Para além das glosas

A mesma abordagem aplica-se a outros campos multilingues. As glosas são uma lista de `Form`, mas as definições e a maioria dos outros campos multilingues são mapeamentos `Multitext` indexados por idioma, pelo que uma edição consiste numa simples atribuição:

```python
sense.definition["en"] = "a cor de uma coisa"
```

Consulte [Texto multilingue](read-edit-write.md#multilingual-text) para saber como funciona o mapeamento.

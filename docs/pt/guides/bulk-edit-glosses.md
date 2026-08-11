# Exemplo prático: edição em massa de glossários

Uma tarefa de manutenção comum: uniformizar a ortografia em todas as entradas em inglês de um léxico (britânica → americana, ou vice-versa) sem alterar qualquer outro aspeto do ficheiro. Este exemplo apresenta um script que carrega, edita, valida e guarda — demonstrando como a API de edição e a garantia de fidelidade funcionam em conjunto.

## O guião

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Retorna todos os sentidos, incluindo os sub-sentidos (recursivo)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
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
    sys.exit(f"interrupção: {len(errors)} erro(s) de validação, nada guardado")

lex.save()
print(f"gloss(es) editado(s) {edited_glosses} em {len(changed)} entrada(s)")
```

Algumas coisas que vale a pena referir:

- `Sense.subsenses` é, por si só, uma `list[Sense]`, pelo que `iter_senses` a percorre de forma recursiva — uma edição em massa que apenas percorresse `entry.senses` ignoraria silenciosamente qualquer gloss aninhado sob um subsense.
- `gloss.text` é um `Text`, não uma string simples: `str(gloss.text)` simplifica-o para efeitos de correspondência, e a substituição é gravada novamente com `sil_lift.Text([new])`, em vez de alterar a string no local.
- A função `lex.changed_entries()` indica quais as entradas que diferem do ficheiro tal como foi carregado. Uma vez que o resumo de uma entrada abrange toda a sua subárvore, uma alteração num sub-significado aninhado é comunicada à entrada que o contém.
  - Como compara conteúdo serializado, a atribuição a um campo do valor que este já possuía não é registada.
  - Apresenta apenas alterações de conteúdo; as funções `lex.added_entries()` e `lex.removed_entries()` abrangem as entradas que surgiram ou desapareceram desde o carregamento.
  - Devolve as próprias entradas, sem que a existência de `id` duplicados ou ausentes (o que o LIFT permite) tenha qualquer influência.
  - Enquanto contagem, só faz sentido quando há algo com que comparar. Quando a camada de passagem se recusa a efetuar a análise byte a byte da fonte — seja devido a uma codificação não compatível com ASCII, seja devido a uma discrepância entre o scanner e o analisador —, não existe uma linha de base e a função `changed_entries()` reporta _todas_ as entradas. Essa é a resposta correta no que diz respeito à proteção contra gravação, uma vez que, nesse caso, o `save()` volta a serializar o ficheiro na íntegra, mas isso significa que a contagem corresponde ao tamanho do léxico e não ao tamanho da edição.
- A função `lex.changes()` indica se o documento sofreu _alguma_ alteração. Abrange não só as entradas, mas também o cabeçalho, o elemento raiz e todos os elementos com a classe `.lift-ranges`.
  - Só é falso quando a função `save()` reproduz os bytes de origem, o que faz com que `if not lex.changes(): ...` seja a forma correta de evitar uma gravação desnecessária. A garantia funciona num único sentido: nunca indica «nada para registar» relativamente a um documento que seria reescrito, enquanto que uma alteração que obrigue a uma resseriação completa pode resultar nos mesmos bytes originais e, mesmo assim, ser registada.
  - Como compara o conteúdo e não o destino, utilize-o apenas para guardar no próprio local: `lex.save(some_other_dir / "dictionary.lift")` grava o documento e os seus ficheiros associados num local que ainda não contém nada, independentemente de ter havido ou não alterações.
  - It is a guard, not a speed-up — answering it digests every entry, which is the same work `save()` does to decide passthrough, so what you skip is the write itself (an untouched mtime, no spurious diff), not the effort of deciding.
- A validação na memória (`lex.iter_problems()`) serializa primeiro o estado editado, para que este reflita corretamente a edição antes de qualquer coisa ser gravada no disco. Interromper a execução perante qualquer `Problem` de nível `"error"` — os avisos são deixados para que o chamador os avalie — significa que uma edição incorreta nunca chega à função `save()`.

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

# Garantias de fidelidade

O LIFT é um formato de _intercâmbio_, pelo que a primeira regra é **nunca ignorar aquilo que não compreendes**. O contrato do `sil-lift`, verificado pelo conjunto de testes em cada execução (ficheiros de corpus e geração baseada em propriedades):

## Leitura

Qualquer documento LIFT 0.13 bem formado é carregado — mesmo que inclua conteúdo inválido em termos de esquema. Tudo o que o modelo não definir é transportado no contentor opaco `Extras` do nó mais próximo como _resíduo LIFT_ — nome dado pelo FieldWorks a este conceito, que é armazenado num campo `LiftResidue`: atributos e elementos desconhecidos, comentários XML e instruções de processamento, texto disperso e atributos tipados malformados (uma data inválida permanece como a cadeia de caracteres original em `Extras`; o campo tipado é `None`).

## Guardar um documento sem alterações

`load()` → `save()`, sem alterações, gera uma **saída byte a byte idêntica** — sem reformatação, sem reescapamento, sem reordenação, incluindo marcas de ordem de bytes e declarações XML. De momento, não existe nenhuma lista de normalização: a identidade é exata.

Exceções (o gravador recorre à serialização canónica completa, que é semanticamente completa, mas não preserva os bytes):

- a codificação da fonte não é compatível com ASCII (não é UTF-8/US-ASCII), ou
- o código-fonte contém um DOCTYPE, ou
- o scanner de bytes e o analisador não estão de acordo quanto à estrutura de nível superior do documento — por exemplo, um segundo `<header>` fora das especificações, que o analisador mantém apenas uma vez (o scanner é deliberadamente conservador: em caso de dúvida, não captura quaisquer bytes da fonte), ou
- o código-fonte foi compilado na memória, em vez de ser carregado a partir de um ficheiro.

## Guardar um documento editado

- **As entradas não alteradas são emitidas tal como estão, a partir dos seus bytes originais.** Uma entrada é considerada alterada se alguma parte do seu objeto-modelo tiver sido alterada desde a análise (detetada através de um instantâneo de serialização canónica, e não por um indicador de alteração).
- **As entradas alteradas são re-serializadas de forma canónica e completa**: UTF-8, indentação com 2 espaços _fora_ do conteúdo misto (os espaços dentro de `<text>` e `<span>` nunca são alterados), um agrupamento de elementos filhos documentado por elemento (por exemplo, entrada: unidade lexical, citação, pronúncias, variantes, sentidos, notas, relações, etimologias, anotações, características, campos), ordem fixa dos atributos, datas em ISO-8601 (`Z` para UTC). Todos os resíduos são reemitidos; a sua posição é restaurada no índice filho original, limitada à nova lista de filhos (uma aproximação — as posições exatas em bytes só são garantidas para entradas que não foram alteradas).
- Adicionar, remover ou reordenar entradas faz com que a estrutura do documento seja novamente serializada, mas continua a emitir, tal como estão, os bytes de todas as entradas que não sofreram alterações.

!!! note "&quot;O XML canónico&quot; aqui apresentado não está relacionado com nenhum outro XML canónico"
    A forma canónica nesta página refere-se à forma documentada do próprio `sil-lift`, descrita num ponto anterior. Não tem qualquer relação com o processo «Canonical XML» (C14N) do W3C. Não tem qualquer relação com a classe `CanonicalXmlSettings` do `SIL.Core`.

## O XML de conteúdo não pode representar

Os caracteres não BMP — emojis, CJK Extension B, Adlam, tudo o que estiver acima de U+FFFF — são conteúdo normal e são transmitidos com idêntica precisão de bytes na ida e na volta. Um «par substituto» é um pormenor da codificação UTF-16: as cadeias de caracteres em Python são sequências de pontos de código, pelo que nem o leitor, nem o analisador de bytes, nem o gravador alguma vez o detetam.

Um caractere de substituição _isolado_ (U+D800–U+DFFF) é diferente: uma cadeia de caracteres em Python pode conter um, mas um documento XML pode não conter, independentemente da codificação. Nunca pode provir de um ficheiro — o analisador rejeita ambas as formas de escrita, uma referência de caractere `&#xD800;` e os bytes CESU-8/WTF-8 — apenas de uma cadeia de caracteres atribuída através da API. Ao guardar esse modelo, é gerado um erro `LiftWriteError` que indica o nome do nó e o ponto de código, sem que seja gravado nada; a validação reporta-o como um único erro `lone-surrogate`, uma vez que o documento não pode ser serializado para que as camadas de esquema o verifiquem.

## Aproximações conhecidas (apenas nós tocados)

- Os comentários _dentro_ de uma execução `<text>` são preservados, mas são movidos para junto da execução, não sendo mantidos na sua posição exata em termos de caracteres.
- A ordem cruzada de elementos filhos dentro de um elemento editado é normalizada para o agrupamento canónico (o `interleave` do esquema LIFT torna esta ordem semanticamente insignificante).
- Um elemento multitext que esteja presente mas que não contenha nada — nem formas, nem resíduos, por exemplo, `<definition></definition>` — não é reemitido. O modelo representa estes campos como um `Multitext` sempre presente (`unidade-lexical`, `citação`, `definição`, o `uso` de uma relação e `rótulo` / `abbrev` / `description` em referências de URL, intervalos, elementos de intervalo e no cabeçalho), pelo que um campo vazio é indistinguível de um ausente após a análise. Não se perde nada em termos semânticos.

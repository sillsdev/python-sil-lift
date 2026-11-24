# Garantias de fidelidade

O LIFT é um formato de _intercâmbio_, pelo que a primeira regra é **nunca ignorar aquilo que não compreendes**. O contrato do `sil-lift`, verificado pelo conjunto de testes em cada execução (ficheiros de corpus e geração baseada em propriedades):

## Leitura

Qualquer documento LIFT 0.13 bem formado é carregado, mesmo que inclua conteúdo inválido em termos de esquema. Tudo o que o modelo não definir é transportado no contentor opaco `Extras` do nó mais próximo como _resíduo LIFT_. (Esse é o nome que o FieldWorks atribui à mesma ideia, que é armazenada num campo `LiftResidue`.) Os resíduos incluem:

- atributos e elementos desconhecidos;
- Comentários e instruções de processamento XML;
- texto isolado;
- atributos tipados com formato incorreto: uma data inválida mantém-se como a cadeia de caracteres original em `Extras`, e o campo tipado é `None`.

## Guardar um documento sem alterações

`load()` → `save()`, sem alterações, gera uma **saída byte a byte idêntica**: sem reformatação, sem reescapamento, sem reordenação, incluindo marcas de ordem de bytes e declarações XML. De momento, não existe nenhuma lista de normalização: a identidade é exata. Os carimbos de data e hora são gerados a partir do conteúdo, pelo que um documento que não tenha sofrido alterações também não tem nenhum carimbo gerado.

Exceções (o gravador recorre à serialização canónica completa, que é semanticamente completa, mas não preserva os bytes):

- a codificação da fonte não é compatível com ASCII (não é UTF-8/US-ASCII), ou
- o código-fonte contém um DOCTYPE, ou
- o analisador de bytes e o analisador sintático não chegam a um consenso quanto à estrutura de nível superior do documento; por exemplo, um segundo `<header>` fora das especificações, que o analisador sintático mantém apenas uma vez, ou
- o código-fonte foi compilado na memória, em vez de ser carregado a partir de um ficheiro.

O analisador de bytes é deliberadamente conservador: em caso de dúvida, não captura nenhum byte de origem.

## Guardar um documento editado

- **As entradas não alteradas são emitidas tal como estão, a partir dos seus bytes originais.** Uma entrada é considerada alterada se alguma parte do seu objeto-modelo tiver sido alterada desde a análise (detetada através de um instantâneo de serialização canónica, e não por um indicador de alteração).
- **As entradas alteradas são novamente serializadas de forma canónica e completa.** A forma canónica é:
  - UTF-8.
  - Recuo de 2 espaços _fora_ do conteúdo misto; os espaços em branco dentro de `<text>` e `<span>` nunca são alterados.
  - Um agrupamento de filhos documentado por elemento; para `<entry>`: unidade lexical, citação, pronúncias, variantes, sentidos, notas, relações, etimologias, anotações, características, campos.
  - Corrigida a ordem dos atributos.
  - Datas no formato ISO-8601 (`Z` para UTC).
- **Todos os resíduos são reemitidos.** A sua posição é restaurada no índice filho original, limitada à nova lista de filhos; trata-se de uma aproximação, uma vez que as posições exatas em bytes só são garantidas para entradas que não tenham sido alteradas.
- Adicionar, remover ou reordenar entradas faz com que a estrutura do documento seja novamente serializada, mas continua a emitir, tal como estão, os bytes de todas as entradas que não sofreram alterações.
- **Uma entrada alterada é marcada** com um novo valor para `dateModified` e, caso não tivesse nenhum, com um valor para `dateCreated`. Consulte [Carimbos de data/hora gerados](#generated-timestamps).

!!! note "&quot;O XML canónico&quot; aqui apresentado não está relacionado com nenhum outro XML canónico"

    A forma canónica nesta página refere-se à forma documentada do próprio `sil-lift`, descrita num ponto anterior. Não tem qualquer relação com o processo «Canonical XML» (C14N) do W3C. Não tem qualquer relação com a classe `CanonicalXmlSettings` do `SIL.Core`.

## Carimbos de data/hora gerados

Um carimbo gerado é o único elemento na saída que não depende da entrada.

### Quais são as entradas que têm carimbo?

- **O que é marcado.** Todas as entradas cujo conteúdo tenha sido alterado desde que foram lidas, com um novo valor para `dateModified` e, caso não tivessem nenhum, um valor para `dateCreated` correspondente ao mesmo momento. Uma edição enviada após a data em que foi carregada parece não ter sido alterada para tudo o que faz a reconciliação com base nesse atributo, incluindo o FieldWorks e a importação LIFT do The Combine.
- **Apenas entradas.** Não deve haver nenhum nó abaixo de um `<entry>`, nem nada no cabeçalho.
- **O que é deixado como está.** Uma entrada cuja data foi definida deliberadamente por quem efetuou a chamada e uma entrada criada após o carregamento que já contém uma data.
- **A remoção de uma data é respeitada.** `entry.date_modified = None`, quando aplicado a uma entrada lida com esse valor, é um valor deliberado como qualquer outro, pelo que a entrada é eliminada sem `dateModified`, independentemente de o seu conteúdo ter sido alterado ou não.
  - Um registo lido sem esse valor é um caso diferente: `None` é o valor que já se encontra lá, indistinguível de nunca ter sido alterado, pelo que uma edição continua a marcá-lo.
- **Uma data que não pode ser analisada é substituída.** Uma data que o modelo não conseguiu analisar é considerada um [resíduo](#reading) em vez de uma data, pelo que um carimbo a substitui e a cadeia de caracteres original é eliminada. É preferível que uma entrada editada inclua uma data real em vez de `dateModified="whenever"`.

### Como se aplica o selo

- **O momento.** UTC com precisão de segundos (`AAAA-MM-DDTHH:MM:SSZ`, o formato utilizado em todas as exportações do FieldWorks que foram analisadas), lido no relógio de parede. Um segundo corresponde a uma data; por isso, uma alteração guardada no espaço de um segundo em relação à anterior recebe o mesmo carimbo.
- **`save(when=...)`** indica o momento em vez da hora do relógio, o que garante que a saída marcada seja reproduzível para um gate de CI baseado em diff. Deve ter em conta o fuso horário e é normalizado para segundos inteiros em UTC.
- **`save(stamp=False)`** guarda o modelo exatamente tal como está, incluindo o resíduo.
- **Registar commits com a escrita `.lift`.** Qualquer coisa que impeça essa escrita de ser aplicada faz com que as datas voltem a ser as anteriores. Assim que acertar, eles ficam de pé, mesmo que um ataque de companheiro que se siga a esse falhe.

## O XML de conteúdo não pode representar

Os caracteres não BMP (emoji, CJK Extension B, Adlam, qualquer coisa acima de U+FFFF) são conteúdo normal e são transmitidos com idêntica precisão de bytes na ida e na volta. Um «par substituto» é um pormenor da codificação UTF-16: as cadeias de caracteres em Python são sequências de pontos de código, pelo que nem o leitor, nem o analisador de bytes, nem o gravador alguma vez o detetam.

Um caractere de substituição _isolado_ (U+D800–U+DFFF) é diferente: uma cadeia de caracteres em Python pode conter um, mas um documento XML pode não conter, independentemente da codificação. Nunca pode provir de um ficheiro, porque o analisador rejeita ambas as formas de escrita (uma referência de carácter `&#xD800;` e os bytes CESU-8/WTF-8). Só pode provir de uma cadeia de caracteres atribuída através da API.

Ao guardar esse modelo, é gerado um erro `LiftWriteError` que indica o nome do nó e o ponto de código, e nada é gravado. A validação assinala isto como um único erro «lone-surrogate», uma vez que o documento não pode ser serializado para que as camadas de esquema o verifiquem.

## Aproximações conhecidas (apenas nós tocados)

- Os comentários _dentro_ de uma execução `<text>` são preservados, mas são movidos para junto da execução, não sendo mantidos na sua posição exata em termos de caracteres.
- A ordem cruzada de elementos filhos dentro de um elemento editado é normalizada para o agrupamento canónico (o `interleave` do esquema LIFT torna esta ordem semanticamente insignificante).
- Um `<form>` ou `<gloss>` sem o atributo `lang` não é reemitido, tal como qualquer elemento que contenha; a validação assinala essa omissão como `form-missing-lang`. Um nó que não tenha sido alterado mantém os seus bytes de origem, pelo que essa forma se mantém até que algo na sua entrada seja editado.
- Um elemento multitexto que esteja presente mas que não contenha nada (sem formas, sem resíduos, por exemplo, `<definition></definition>`) não é reemitido. Não se perde nada em termos semânticos.
  - O modelo representa estes campos como um `Multitext` sempre presente, pelo que, após a análise, um campo vazio é indistinguível de um campo ausente. Os campos são `lexical-unit`, `citation`, `definition`, o `usage` de uma relação e `label` / `abbrev` / `description` em referências de URL, intervalos, elementos de intervalo e no cabeçalho.

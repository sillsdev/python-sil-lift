# A linha de comandos (CLI)

Ao instalar o pacote (`pip install sil-lift`), também é instalado o comando `sil-lift`.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    todos os problemas, com indicação de ficheiro/entrada/linha; sai com código de saída 1 em caso de erros

sil-lift stats PATH [--format {text,json}]
    contagens de entradas/sentidos/línguas (em fluxo contínuo; qualquer tamanho)

sil-lift sort PATH [-o OUT]
    cópia ordenada canonicamente, pronta para comparação (por predefinição: no local)

sil-lift check-media PATH
    relatório de meios em falta, com erros ortográficos e órfãos; sai com código de saída 1 se houver meios em falta ou com erros ortográficos

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    uma linha por sentido de folha (subsentidos nivelados) para CSV/TSV (transmissão contínua)
```

## validar

O comando `validate` apresenta uma linha por resultado e, em seguida, um resumo. `--format json` apresenta os mesmos resultados sob a forma de um único objeto JSON:

```
$ sil-lift validate dictionary.lift
aviso [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Letra de unidade do Windows utilizada como autoridade URI (no estilo FLEx: file://C:/)
erro [dangling-ref] dictionary.lift:88 (entrada poʻo_a1b2): a referência «nope» não corresponde a nenhum ID/GUID de entrada nem a nenhum ID de sentido
1 erro(s), 1 aviso(s)

$ sil-lift validate dictionary.lift --format json
{
  «problems»: [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Letra de unidade do Windows utilizada como autoridade URI (file://C:/ ao estilo FLEx)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "a referência 'nope' não corresponde a nenhum id/guid de entrada nem a nenhum id de sentido",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

Opções do `validate`:

- `--format json` escreve um único objeto JSON na saída padrão (e nada mais) para utilização em CI/automatização. Consulte o esquema no exemplo acima.
- A opção `--strict` trata os avisos como erros, terminando com o código de saída 1 caso seja detetado algum. Utilize-o para condicionar a execução de uma compilação à ausência total de avisos, em vez de apenas à ausência de erros.
- `--no-check-media` ignora a verificação da presença de suportes no sistema de ficheiros, suprimindo os resultados `missing-media` e `media-href-mismatch`. Útil quando os ficheiros de áudio e de fotografias de uma exportação estão guardados noutro local ou ainda não foram copiados para junto do ficheiro `.lift`.
- `--allow CODE[,CODE...]` (repetível) apresenta os resultados relativos aos códigos indicados, mas não os tem em conta na decisão de aprovação/reprovação.
  - Isto aplica-se tanto a erros como a avisos, pelo que um aviso permitido também não ativa a opção `--strict`.
  - A linha de resumo contabiliza as ocorrências permitidas por código; o campo `allowed` do resumo em JSON apresenta o respetivo total.
  - Um código que nunca ocorre é ignorado, pelo que uma lista de permissões continua a funcionar mesmo que uma verificação seja retirada.
- O `--require-ids` também falha (com um erro `missing-id`) em qualquer entrada que não tenha um `guid` ou em que falte um `id`. Isso é mais rigoroso do que o LIFT, no caso de fluxos de trabalho que reimportam através de um identificador estável.

Se passar `-` como caminho, o documento é lido a partir do stdin. Um documento transmitido não tem pasta, pelo que o ficheiro `.lift-ranges` associado e os ficheiros multimédia não são resolvidos.

!!! note

    Os códigos de saída do `validate` e o esquema `--format json` constituem uma interface de automatização suportada: ambos são abrangidos por testes e só sofrem alterações de acordo com a SemVer.

## estatísticas

```
$ sil-lift stats sango.lift
entradas:   3507
detecções:    4541
...
```

O `stats` também aceita a opção `--format json`, apresentando as contagens como um único objeto JSON.

## ordenar

O `sort` reescreve apenas o ficheiro `.lift`; os ficheiros `.lift-ranges` associados permanecem inalterados (organize-os separadamente com a [API `RangesFile`](folder-media.md#ranges)).

## exportação

A função `export` escreve uma linha por sentido de folha. `--langs` determina quais as línguas que recebem as colunas `gloss_` e `definition_`; por predefinição, estas são detetadas a partir do documento.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## Pacotes compactados

As opções `validate`, `stats`, `check-media` e `export` também aceitam um pacote LIFT compactado (`.zip`). Os seus ficheiros podem estar na raiz do arquivo ou dentro de uma pasta de nível superior. Tudo o que um comando extrai é guardado num diretório temporário e é eliminado quando o comando termina.

- Os comandos de streaming `stats` e `export` extraem apenas o próprio ficheiro `.lift`, pelo que mantêm um baixo custo em pacotes com grande volume de dados multimédia.
- As funções `validate` e `check-media` precisam da pasta completa e extraem todo o seu conteúdo.

## Codificação de saída

Toda a saída é em UTF-8, em todas as plataformas, quer seja direcionada para um console, um pipe ou um redirecionamento `>`. Nunca é a codificação da localização (cp1252 no Windows, ASCII numa localização C/POSIX) que não consegue representar o conteúdo LIFT. O comando `sil-lift export dictionary.lift > dictionary.csv` grava, portanto, exatamente os bytes que o comando `-o dictionary.csv` grava, incluindo os terminadores de linha CRLF.

## Códigos de saída

- `0`: sucesso. Os avisos não fazem com que a execução falhe, a menos que se utilize a opção `--strict`.
- `1`: conclusões. Um erro de validação, dados ausentes ou com erros ortográficos, ou um aviso quando se utiliza a opção `--strict` resulta na saída 1, a menos que o respetivo código tenha sido especificado na opção `--allow`.
- `2`: Falha de E/S. Não foi possível ler a entrada ou escrever a saída, por exemplo, porque o disco está cheio ou porque um programa de leitura, como o `head`, fechou o canal.

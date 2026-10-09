# A linha de comandos

A instalação do pacote (`pip install sil-lift`) instala também o comando `sil-lift` — uma ferramenta compatível, no espírito do LiftTools, que vem incluída no pacote (e, no caso do `validate`, um exemplo prático da API da biblioteca).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--allow CODE[,CODE...]]...
                  [--require-ids]
                                           todos os problemas, com ficheiro/entrada/linha; sai com código de saída 1 em caso de erros
sil-lift stats PATH [--format {text,json}]
                                           contagens de entradas/sentidos/línguas (em fluxo; qualquer tamanho)
sil-lift sort PATH [-o OUT]               cópia ordenada canonicamente, pronta para comparação (predefinição: no local)
sil-lift check-media PATH                 relatório de meios em falta, com erros ortográficos e órfãos; sai com código de saída 1 se houver meios em falta ou com erros ortográficos
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           uma linha por sentido folha (subsentidos nivelados) para CSV/TSV (transmissão contínua)
```

Opções do `validate`:

- `--format json` escreve um único objeto JSON na saída padrão (e nada mais) para utilização em CI/automatização; consulte o esquema no exemplo abaixo.
- A opção `--strict` trata os avisos como erros, devolvendo o valor 1 caso seja detetado algum — utilize-a para condicionar a compilação à ausência total de avisos, em vez de apenas à ausência de erros.
- `--no-check-media` ignora a verificação da presença de suportes no sistema de ficheiros, suprimindo os resultados `missing-media` e `media-href-mismatch`. Útil para validar uma exportação recém-gerada cujos ficheiros de áudio/fotografias se encontram noutro local e não na mesma pasta.
- `--allow CODE[,CODE...]` (repetível) apresenta os resultados relativos aos códigos indicados, mas não os tem em conta na decisão de aprovação/reprovação. Isto aplica-se tanto a erros como a avisos, pelo que um aviso permitido também não ativa a opção `--strict`. A linha de resumo contabiliza as ocorrências permitidas por código; o campo `allowed` do resumo em JSON apresenta o respetivo total. Um código que nunca ocorre é ignorado, pelo que uma lista de permissões continua a funcionar após a retirada de uma verificação.
- `--require-ids` também falha (com um erro `missing-id`) em qualquer entrada que não tenha um `guid` ou em qualquer sentido que não tenha um `id` — sendo mais rigoroso do que o LIFT, para fluxos de trabalho que reimportam através de um id estável.

Se passar `-` como caminho, o documento é lido a partir do stdin. Um documento transmitido não tem pasta, pelo que o ficheiro `.lift-ranges` associado e os ficheiros multimédia não são resolvidos.

O `stats` também aceita a opção `--format json`, apresentando as contagens como um único objeto JSON.

!!! note
    Os códigos de saída do `validate` e o esquema `--format json` constituem uma interface de automatização suportada: ambos são abrangidos por testes e só sofrem alterações de acordo com a SemVer.

O `sort` reescreve apenas o ficheiro `.lift`; os ficheiros `.lift-ranges` associados permanecem inalterados
(organize-os separadamente com a API `RangesFile`).

Os comandos `validate`, `stats`, `check-media` e `export` também aceitam um pacote LIFT compactado (um ficheiro `.zip` com qualquer um dos dois formatos — ficheiros na raiz do arquivo ou aninhados numa pasta de nível superior); este é extraído para um diretório temporário e eliminado quando o comando termina. Os comandos de streaming `stats` e `export` extraem apenas o próprio ficheiro `.lift`, pelo que o seu custo de execução é reduzido em pacotes com muitos ficheiros multimédia; os comandos `validate` e `check-media` necessitam da pasta completa e extraem todo o seu conteúdo.

Exemplos:

```
$ sil-lift validate dictionary.lift
erro [dangling-ref] dictionary.lift:88 (entrada apu): a referência «nope» não corresponde a nenhum ID/GUID de entrada nem a nenhum ID de sentido
aviso [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Letra de unidade do Windows utilizada como autoridade URI (file://C:/ ao estilo FLEx)
1 erro(s), 1 aviso(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "a referência 'nope' não corresponde a nenhum ID de entrada/GUID ou ID de sentido",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Letra de unidade do Windows utilizada como autoridade URI (file://C:/ ao estilo FLEx)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}

$ sil-lift stats sango.lift
entradas:   3507
sentidos:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Toda a saída é em UTF-8, em todas as plataformas e independentemente de ser direcionada para um console, um pipe ou um redirecionamento `>` — nunca na codificação da localização (cp1252 no Windows, ASCII numa localização C/POSIX), que não consegue representar conteúdo LIFT. O comando `sil-lift export dictionary.lift > dictionary.csv` grava, portanto, exatamente os bytes que o comando `-o dictionary.csv` grava, incluindo os terminadores de linha CRLF.

Códigos de saída: `0` sucesso (os avisos não provocam falha na execução, a menos que se utilize a opção `--strict`), `1` resultados (erros de validação / meios ausentes ou com erros ortográficos / avisos quando se utiliza a opção `--strict`, sem contar os códigos atribuídos à opção `--allow`), `2` uma falha de E/S em qualquer uma das extremidades — entrada que não pode ser lida ou saída que não pode ser gravada (um leitor como o `head` a fechar o canal, um disco cheio).

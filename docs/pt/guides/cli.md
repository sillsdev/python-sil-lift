# A linha de comandos

Ao instalar o pacote (`pip install sil-lift`), é também instalado o comando `sil-lift` — uma ferramenta compatível com o estilo LiftTools que vem incluída no pacote (e, no caso de `validate`, um exemplo prático da API da biblioteca).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           todos os problemas, tratados por entrada/linha; saída 1 em caso de erros
sil-lift stats PATH [--format {text,json}]
                                           contagens por entrada/sentido/língua (em fluxo; qualquer tamanho)
sil-lift sort PATH [-o OUT]               cópia ordenada canonicamente, pronta para comparação (predefinição: no local)
sil-lift check-media PATH                 relatório de meios em falta e órfãos; sai com código 1 se houver meios em falta
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           uma linha por sentido folha (subsentidos achatados) para CSV/TSV (streaming)
```

`--format json` escreve um único objeto JSON na saída padrão (e nada mais) para utilização em CI/automatização; consulte o esquema no exemplo abaixo. A opção `--strict` trata os avisos como erros, devolvendo o valor 1 caso seja detetado algum — utilize-a para condicionar a conclusão da compilação à ausência total de problemas, em vez de apenas à ausência de erros. `--no-check-media` ignora a verificação da presença de suportes no sistema de ficheiros (suprimindo os resultados de `missing-media`), o que é útil ao validar uma exportação recém-gerada cujos ficheiros de áudio/fotografias se encontram noutro local e não estão armazenados no mesmo disco. `--require-ids` também falha (com um erro `missing-id`) em qualquer entrada que não tenha um `guid` ou em qualquer sentido que não tenha um `id` — sendo mais rigoroso do que o LIFT, para fluxos de trabalho que reimportam através de um id estável. Ao passar `-` como caminho, o documento é lido a partir do stdin (um documento transmitido por canalização não tem pasta, pelo que o ficheiro `.lift-ranges` associado e os ficheiros multimédia não são resolvidos). O `stats` também aceita a opção `--format json`, apresentando as contagens como um único objeto JSON.

!!! note
    Os códigos de saída do `validate` e o esquema `--format json` constituem uma interface de automatização suportada: ambos são abrangidos por testes e só sofrem alterações de acordo com a SemVer.

O `sort` reescreve apenas o ficheiro `.lift`; os ficheiros `.lift-ranges` associados permanecem inalterados
(organize-os separadamente com a API `RangesFile`).

Os comandos `validate`, `stats`, `check-media` e `export` também aceitam um pacote LIFT compactado (um ficheiro `.zip` com qualquer um dos dois formatos — ficheiros na raiz do arquivo ou aninhados numa pasta de nível superior); este é extraído para um diretório temporário e eliminado quando o comando termina.

Exemplos:

```
$ sil-lift validate dictionary.lift
erro [dangling-ref] dictionary.lift:88 (entrada apu): a referência «nope» não corresponde a nenhum ID/GUID de entrada nem a nenhum ID de sentido
aviso [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Letra de unidade do Windows utilizada como autoridade URI (estilo FLEx file://C:/)
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
    "warnings": 1
  }
}

$ sil-lift stats sango.lift
entradas:   3507
sentidos:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Códigos de saída: `0` sucesso (são permitidos avisos, a menos que se utilize a opção `--strict`), `1` resultados (erros de validação / ficheiros multimédia em falta / avisos quando se utiliza a opção `--strict`), `2` entrada ilegível.

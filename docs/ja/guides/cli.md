# コマンドライン（CLI）

パッケージをインストールすると（`pip install sil-lift`）、`sil-lift` コマンドも一緒にインストールされます。

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    すべての問題（ファイル/エントリ/行を指定）；エラー時は終了コード 1

sil-lift stats PATH [--format {text,json}]
    エントリ/意味/言語の件数（ストリーミング；サイズ不問）

sil-lift sort PATH [-o OUT]
    正規順にソートされ、差分比較可能なコピー（デフォルト：その場で処理）

sil-lift check-media PATH
    欠落、スペルミス、孤立したメディアのレポート。欠落またはスペルミスの場合は終了コード 1 を返す

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    リーフセンスごとに1行（サブセンスは平坦化）でCSV/TSVに出力（ストリーミング）
```

## 検証する

`validate` は、検出結果ごとに1行ずつ出力し、その後に要約を表示します。 `--format json` を指定すると、1つのJSONオブジェクトとして同じ結果が得られます：

```
$ sil-lift validate dictionary.lift
警告 [uri-not-rfc] dictionary.lift:6:<range href='file://C:/...'>: URIの権限としてWindowsのドライブ文字が使用されています (FLEx形式の file://C:/)
エラー [dangling-ref] dictionary.lift:88 (エントリ poʻo_a1b2): 参照 'nope' に一致するエントリ ID/GUID または意味 ID がありません
エラー 1 件、警告 1 件

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: URI 権限として Windows ドライブ文字が使用されています (FLEx 形式の file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' は、どのエントリ ID/GUID またはセンス ID とも一致しません",
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

`validate` のオプション：

- `--format json` を指定すると、CIや自動化処理で利用できるよう、単一のJSONオブジェクトが標準出力に書き出されます（それ以外は何も出力されません）。上記の例のスキーマをご覧ください。
- `--strict` オプションを指定すると、警告がエラーとして扱われ、警告が見つかった場合は終了値 1 を返します。これを使って、エラーだけでなく、警告が一切ない場合にのみビルドを停止するように設定します。
- `--no-check-media` を指定すると、ファイルシステムのメディア存在確認がスキップされ、`missing-media` および `media-href-mismatch` の検出結果が表示されなくなります。エクスポートしたオーディオファイルや写真ファイルが別の場所に保存されている場合や、まだ `.lift` ファイルの隣にコピーされていない場合に便利です。
- `--allow CODE[,CODE...]`（複数指定可）は、指定されたコードに関する検出結果を報告しますが、合格／不合格の判定には反映しません。
  - これはエラーと警告の両方に適用されるため、許容される警告であっても `--strict` が発動することはありません。
  - 要約行には、コードごとの「許可された」結果の件数が集計されています。JSON要約の `allowed` には、それらの合計値が示されています。
  - 一度も発生しないコードは無視されるため、チェックが廃止されても許可リストは引き続き機能します。
- `--require-ids` は、`guid` がないエントリや、`id` がないセンスに対しても、さらにエラー（`missing-id` エラー）が発生します。これは、安定したIDを使用して再インポートを行うワークフローにおいて、LIFTよりも厳格な仕様となっています。

パスとして `-` を指定すると、stdin からドキュメントが読み込まれます。パイプ処理されたドキュメントにはフォルダがないため、それに付随する `.lift-ranges` ファイルやメディアは解決されません。

!!! note

    `validate` の終了コードおよび `--format json` のスキーマは、サポートされている自動化インターフェースです。これらはいずれもテストの対象となっており、SemVer に基づいてのみ変更されます。

## 統計

```
$ sil-lift stats sango.lift
エントリ数:   3507
検知数:    4541
...
```

`stats` も同様に `--format json` を受け付け、集計結果を単一の JSON オブジェクトとして出力します。

## 並べ替え

`sort` は `.lift` ファイルのみを上書きします。関連する `.lift-ranges` ファイルは変更されません（これらをソートするには、[`RangesFile` API](folder-media.md#ranges) を使用して別途処理してください）。

## エクスポート

`export` は、リーフセンスごとに1行ずつ書き出します。 `--langs` は、`gloss_` および `definition_` 列がどの言語に対して生成されるかを指定します。デフォルトでは、これらは文書から自動的に検出されます。

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## ZIP形式のパッケージ

`validate`、`stats`、`check-media`、および`export`も、zip形式（`.zip`）のLIFTパッケージを受け付けます。そのファイルは、アーカイブのルートディレクトリに配置することも、あるトップレベルフォルダ内に配置することもできます。コマンドによって抽出されたものはすべて一時ディレクトリに保存され、コマンドの実行終了時に破棄されます。

- ストリーミングコマンド `stats` および `export` は、`.lift` ファイルそのもののみを抽出するため、データ量の多いパッケージでも処理負荷が低くなります。
- `validate` と `check-media` では、フォルダ全体が必要であり、その内容をすべて抽出する必要があります。

## 出力エンコーディング

すべての出力は、どのプラットフォームであっても、またコンソール、パイプ、あるいは `>` によるリダイレクトのいずれに出力される場合でも、UTF-8 形式となります。 LIFTコンテンツを表現できないのは、決してロケールエンコーディング（Windowsではcp1252、C/POSIXロケール下ではASCII）ではありません。 `sil-lift export dictionary.lift > dictionary.csv` を実行すると、`-o dictionary.csv` が書き出すのと同じバイト列が書き出され、CRLF 行末区切り文字も含まれます。

## 終了コード

- `0`: 成功。 `--strict` オプションが指定されていない限り、警告があっても実行は失敗しません。
- `1`: 調査結果。検証エラー、メディアの欠落やスペルミス、あるいは `--strict` オプション指定時の警告が発生した場合、そのコードが `--allow` オプションで指定されていない限り、終了コード 1 となります。
- `2`: I/O エラー。ディスクが満杯である、あるいは`head`のようなリーダーがパイプを閉じたなどの理由により、入力を読み取れなかったか、出力を書き込めませんでした。

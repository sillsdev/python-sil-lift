# コマンドライン

パッケージをインストールすると（`pip install sil-lift`）、`sil-lift` コマンドもインストールされます。これは、LiftTools の精神に基づいた、パッケージに同梱されているサポートツールです（また、`validate` については、ライブラリ API の実用例も含まれています）。

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--allow CODE[,CODE...]]...
                  [--require-ids]
                                           ファイル/エントリ/行を含むすべての問題；エラー時には終了コード 1 を返す
sil-lift stats PATH [--format {text,json}]
                                           エントリ/センス/言語のカウント（ストリーミング；サイズ不問）
sil-lift sort PATH [-o OUT]               正規化されたソート済み、差分比較可能なコピー（デフォルト：その場更新）
sil-lift check-media PATH                 欠落、スペルミス、孤立したメディアのレポート；欠落またはスペルミスの場合は 1 で終了
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           リーフセンスごとに1行（サブセンスは平坦化）でCSV/TSV形式に出力（ストリーミング）
```

`validate` のオプション：

- `--format json` を指定すると、CIや自動化処理で使用できるよう、単一のJSONオブジェクトが標準出力に書き出されます（それ以外は何も出力されません）。スキーマについては、以下の例を参照してください。
- `--strict` オプションは、警告をエラーとして扱い、警告が見つかった場合は終了値 1 を返します。エラーだけでなく、警告が一切ない場合にのみビルドを成功させるようにしたい場合にこのオプションを使用してください。
- `--no-check-media` を指定すると、ファイルシステムのメディア存在確認がスキップされ、`missing-media` および `media-href-mismatch` の検出結果が表示されなくなります。オーディオファイルや写真ファイルが同じフォルダ内ではなく別の場所に保存されている、生成されたばかりのエクスポートデータを検証する際に便利です。
- `--allow CODE[,CODE...]`（複数指定可）は、指定されたコードに関する検出結果を報告しますが、合格／不合格の判定には反映しません。これはエラーと警告の両方に適用されるため、許容される警告であっても `--strict` が発動することはありません。要約行には、コードごとの「許可された」結果の件数が集計されています。JSON要約の `allowed` には、それらの合計値が示されています。一度も発生しないコードは無視されるため、チェックが廃止された後も許可リストは引き続き機能します。
- `--require-ids` は、`guid` がないエントリや `id` がないセンスに対しても（`missing-id` エラーとして）失敗します。これは、安定した ID を使用して再インポートを行うワークフローにおいて、LIFT よりも厳格な仕様となっています。

パスとして `-` を指定すると、stdin からドキュメントが読み込まれます。パイプ処理されたドキュメントにはフォルダがないため、それに付随する `.lift-ranges` ファイルやメディアは解決されません。

`stats` も同様に `--format json` を受け付け、集計結果を単一の JSON オブジェクトとして出力します。

!!! note
    `validate` の終了コードおよび `--format json` のスキーマは、サポートされている自動化インターフェースです。これらはいずれもテストの対象となっており、SemVer に基づいてのみ変更されます。

`sort` は `.lift` ファイルのみを上書きします。関連する `.lift-ranges` ファイルは変更されません
（これらを並べ替えるには、`RangesFile` API を別途使用してください）。

`validate`、`stats`、`check-media`、および `export` も、ZIP形式のLIFTパッケージ（アーカイブのルートにファイルが配置されている形式、またはトップレベルのフォルダの下にネストされている形式のいずれかの `.zip` ファイル）を受け付けます。このパッケージは一時ディレクトリに展開され、コマンドの実行完了後に削除されます。ストリーミングコマンド `stats` および `export` は `.lift` ファイルのみを抽出するため、メディアデータが大量に含まれるパッケージでも処理負荷が低くなります。一方、`validate` および `check-media` はフォルダ全体を必要とし、その内容をすべて抽出します。

例：

```
$ sil-lift validate dictionary.lift
エラー [dangling-ref] dictionary.lift:88 (エントリ apu): 参照 'nope' に一致するエントリ ID/GUID または意味 ID が見つかりません
警告 [uri-not-rfc] dictionary.lift:6:<range href='file://C:/...'>: URI 権限として Windows ドライブ文字が使用されています (FLEx 形式の file://C:/)
エラー 1 件、警告 1 件

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' matches no entry id/guid or sense id",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: URIの権限としてWindowsのドライブ文字が使用されています（FLEx形式の file://C:/）",
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
entries:   3507
senses:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

すべての出力は、どのプラットフォームであっても、またコンソール、パイプ、あるいは `>` によるリダイレクトのいずれに出力される場合でも、UTF-8 形式となります。LIFT コンテンツを表現できないロケールエンコーディング（Windows では cp1252、C/POSIX ロケール下では ASCII）が使用されることは決してありません。 `sil-lift export dictionary.lift > dictionary.csv` を実行すると、`-o dictionary.csv` が書き出すのと同じバイト列が書き出され、CRLF 行末区切り文字も含まれます。

終了コード：`0`：成功（`--strict` オプションが指定されていない限り、警告は実行の失敗とはみなされない）、`1`：問題が見つかった（検証エラー／メディアの欠落やスペルミス／`--strict` オプション下での警告。ただし、`--allow` オプションで指定されたコードは除く）、 `2` いずれかの端での I/O エラー — 読み取れない入力、または書き込めない出力（`head` のようなリーダーがパイプを閉じた場合、ディスクが満杯の場合など）。

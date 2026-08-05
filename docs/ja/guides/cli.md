# コマンドライン

パッケージをインストールすると（`pip install sil-lift`）、`sil-lift` コマンドもインストールされます。これは、パッケージに同梱されている、LiftTools スタイルのサポート対象ツールです（また、`validate` については、ライブラリ API の実用例も含まれています）。

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           すべての問題、エントリ/行単位で対処；エラー時は終了コード 1
sil-lift stats PATH [--format {text,json}]
                                           エントリ/センス/言語のカウント（ストリーミング；サイズ不問）
sil-lift sort PATH [-o OUT]               正規化されたソート済み、差分比較可能なコピー（デフォルト：その場更新）
sil-lift check-media PATH                 欠落および孤立したメディアのレポート；欠落がある場合は 1 で終了
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           リーフセンスごとに1行（サブセンスは平坦化）でCSV/TSV形式に出力（ストリーミング）
```

`--format json` を指定すると、CIや自動化処理で使用できるよう、単一のJSONオブジェクトが標準出力に書き出されます（それ以外は何も出力されません）。スキーマについては、以下の例を参照してください。 `--strict` オプションは、警告をエラーとして扱い、警告が見つかった場合は終了値 1 を返します。エラーだけでなく、ビルドが完全に正常であることを条件としてビルドを許可したい場合にこのオプションを使用してください。 `--no-check-media` オプションを指定すると、ファイルシステムのメディア存在確認がスキップされ（`missing-media` の検出結果が表示されなくなります）。これは、生成されたばかりのエクスポートを検証する際、オーディオや写真ファイルが別の場所にあり、ディスク上に同じ場所には存在しない場合に役立ちます。 `--require-ids` は、`guid` がないエントリや `id` がないセンスに対しても（`missing-id` エラーとして）失敗します。これは、安定した ID を使用して再インポートを行うワークフローにおいて、LIFT よりも厳格な仕様となっています。 パスとして `-` を指定すると、ドキュメントは標準入力（stdin）から読み込まれます（パイプで渡されたドキュメントにはフォルダがないため、それに付随する `.lift-ranges` やメディアは解決されません）。 `stats` も同様に `--format json` を受け付け、集計結果を単一の JSON オブジェクトとして出力します。

!!! note
    `validate` の終了コードおよび `--format json` のスキーマは、サポートされている自動化インターフェースです。これらはいずれもテストの対象となっており、SemVer に基づいてのみ変更されます。

`sort` は `.lift` ファイルのみを上書きします。関連する `.lift-ranges` ファイルは変更されません
（これらを並べ替えるには、`RangesFile` API を別途使用してください）。

`validate`、`stats`、`check-media`、および `export` も、ZIP形式のLIFTパッケージ（アーカイブのルートにファイルが配置されている形式、またはトップレベルのフォルダの下にネストされている形式のいずれかの `.zip` ファイル）を受け付けます。このパッケージは一時ディレクトリに展開され、コマンドの実行完了後に削除されます。

例：

```
$ sil-lift validate dictionary.lift
エラー [dangling-ref] dictionary.lift:88 (エントリ apu): 参照 'nope' に一致するエントリ ID/GUID または意味 ID がありません
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
      "message": "<range href='file://C:/...'>: URIの権限としてWindowsのドライブ文字が使用されています (FLEx形式の file://C:/)",
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
entries:   3507
senses:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

終了コード：`0`：成功（`--strict` オプションが指定されていない限り、警告は許容される）、`1`：問題が見つかった（検証エラー／メディアの欠落／`--strict` オプション指定時の警告）、`2`：入力が読み取れない。

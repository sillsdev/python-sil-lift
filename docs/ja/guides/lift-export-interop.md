# 準拠したLIFTの生成

このガイドは、LIFT _エクスポーター_ を開発するすべての方を対象としています。つまり、他のアプリケーションのデータモデルを LIFT 0.13 形式に変換する、あらゆる言語で書かれたコードを開発する方に向けたものです。 `sil-lift`は、その作業において2つの役割を果たしています：

- スキーマと、スキーマでは表現できないセマンティクスの両方に照らして出力を検証する適合性チェック機能；
- 出力時に従うべき形状やテキストのルールに関する指針。

LIFTの記述は、その解析よりもはるかに簡単です。エクスポート機能は、自身のモデルが生成する構文のサブセットのみを出力するため、仕様全体のオプション性に対処する必要が一切ないからです。難しいのは細部（`.lift-ranges` コンパニオン、文字体系ごとのテキスト、安定した ID、および XML エスケープ）ですが、それらはまさに以下のチェックで検出される部分です。

## ZIP形式のパッケージ

LIFTは通常、単一の`.zip`ファイルとして移動されます。FieldWorksとThe Combineは、どちらもこの形式でインポートおよびエクスポートを行います。 `sil-lift` は、アーカイブのルートにファイルが配置されている場合と、トップレベルのフォルダの下にネストされている場合という、エコシステムで採用されているいずれのレイアウトにおいても、zip形式のパッケージを直接読み書きします。

### パッケージの内容を読む

`sil_lift.load("package.zip")` は、一時ディレクトリに解凍し、単一の `.lift` ファイルを検索して読み込みます（コンパニオンやメディアは通常通り解決されます）。

- `validate`、`stats`、`check-media`、および`export`の各CLIコマンドも`.zip`形式のパスを指定できるため、以下のゲートはパッケージをそのままの状態で実行します。
- `stats` および `export` ストリームから、パッケージ全体ではなく `.lift` のみを抽出します。メディアが大量に含まれる場合でも価格は安く抑えられ、抽出制限は `.lift` 自体にのみ適用され、その周囲の要素には適用されません。
- 抽出の上限は10 GiBおよび100,000件です。いずれかの制限を超えるパッケージは、`LiftParseError` が発生して拒否されます。また、メンバーのパスが抽出ディレクトリの範囲外にあるパッケージも同様に拒否されます。

### パッケージの作成

`Lexicon.save_zip("out.zip", wrap_folder="MyDict")` は、`.lift`、その `.lift-ranges`、およびソースフォルダ内のその他のすべてのファイル（media、`WritingSystems/`、`consent/` など）をまとめてパッケージ化します。 zipファイルにまとめる。

- `wrap_folder` のデフォルト値は、zip ファイル名と同じ名前の最上位フォルダです（FieldWorks/Combine のインポート規約に従います）。フラットなアーカイブにする場合は、`False` を指定してください。
- 読み込み後に内容が変更されたエントリには、`save()` と同様に、書き込み時に新しい `dateModified` が付与されます。
  - パッケージは、インポートツールが照合を行う対象となるため、そこに古い日付が設定されていると、更新された辞書が未変更のように見えてしまいます。
  - `save()` と同じ `stamp=` および `when=` オプションを受け付けます。詳細は [スタンプの適用方法](../fidelity.md#how-the-stamp-is-applied) を参照してください。

`.lift` および `.lift-ranges` は、パッケージ内ではバイト単位の忠実性を維持しますが、zip コンテナ自体はバイト単位で再現可能ではありません。

## 出力を適合性ゲートとして検証する

`sil-lift validate` コマンドを `.lift` ファイルに向ける。 `.lift` およびそのコンパニオンである `.lift-ranges` の両方に RELAX NG を適用するほか、文法では表現できないセマンティックチェックも行います：

- `relation`/`variant` の未解決参照；
- 重複するGUID;
- 範囲要素の親との整合性;
- その範囲内で定義されていない特性および文法情報の値；
- ヘッダー `range/@href` の参照先が、対応する要素に解決されないもの。

CIでは、何か問題が発生した場合は失敗とし、機械可読な結果を出力する：

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` を指定すると、エラーだけでなく警告も実行の失敗原因となります。
- `--no-check-media` を指定すると、ファイルシステムのメディア存在確認がスキップされます。CIにおいて、オーディオファイルや写真ファイルが `.lift` ファイルと同じフォルダにない場合、この確認で検出される `missing-media` の結果はノイズとなるためです。
- `--format json` を指定すると、人間が読みやすいテキストの代わりに単一の JSON オブジェクト (`{"problems": [...], "summary": {...}}`) が出力されます。その終了コードとスキーマは、SemVer に準拠したサポート対象のインターフェースとなっています（[コマンドラインガイド](cli.md)を参照してください）。
- `--allow CODE[,CODE...]`（繰り返し指定可能）は、FLExの`uri-not-rfc`などの許容されるコードについて、実行が失敗しないようにします。その調査結果は印刷されているが、集計はされていない。
- `--require-ids` オプションを指定すると、`guid` が欠落しているエントリや `id` が欠落しているエントリに対して追加でエラーが発生します。これは、後で再インポートを行う際に、重複を避けるために更新のみを行う必要がある場合に役立ちます。

### 知らぬ間に起こるデータ損失への対策

「サイレントデータ損失」とは、CSVへのフラットなエクスポートでデータが失われる原因となる障害モードのことです。ソースモデルに対して `stats --format json` を実行してカウント情報を取得することで、これを防ぐことができます：

```
sil-lift の統計データのエクスポート export.lift --format json
```

このレポートでは、`entries`、`senses`、`examples`、`media_refs`、`languages`、および名称ごとの`traits`の件数が報告されます。

### Pythonツールチェーンを使用せずにgateを実行する

TypeScript または C# プロジェクトの CI では、Python をインストールしなくても、バンドルされている GitHub Action を通じて同じチェックを実行できます：

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    allow: "uri-not-rfc"
    format: json
```

あるいは、リポジトリの `Dockerfile` からビルドされたコンテナイメージ：

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## `.lift-ranges` コンパニオン

統制語彙（品詞、意味領域、およびその他の特性に基づく値のセット）は、`<header>` から参照される、同階層の `.lift-ranges` ファイルに格納されています：

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

このガイドブックには、各シリーズの完全な定義が掲載されています。値は `<range-element>` です。`parent` は階層を構築します。`label` / `abbrev` / `description` はマルチテキストです：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>名詞</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>鳥</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

エントリは、ID によって値を参照します。例えば、品詞は `<grammatical-info value="Noun"/>`、意味領域は `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>` となります。 `sil-lift validate` はその参照をチェックするため、データが実際に使用している範囲を指定してください：

- その範囲内で定義されていない値は、`undefined-range-value` 警告となります。
- 兄弟IDではない `parent` は、`range-parent` エラーとなります。

これらの比較はNFC正規化に基づいているため、IDと、それを参照する値または`parent`との間で、Unicodeの正規化が異なる場合があります。その違いは、エラーではなく「正規化の不一致」という警告です。とはいえ、可能であれば一貫性のある正規化を1つ定義してください。生の文字列を比較するクライアントは、それらの参照を解決できないからです。「範囲とメディア」も参照してください（folder-media.md）。

Pythonでエクスポートを構築する場合、`Lexicon.add_ranges_file()`、`RangesFile.add_range()`、および`Range.add_element()`がコンパニオンを構築し、ヘッダー参照を自動的に追加してくれます。 `open_writer(..., ranges=...)` は、ストリーミングパス上でも同様の処理を行います。

## テキストおよびマルチテキスト

LIFT におけるすべての自然言語文字列は _マルチテキスト_ です。つまり、各文字体系ごとに 1 つの `<form>` があり、それぞれが `<text>` を囲んでいます：

```xml
<lexical-unit>
  <form lang="seh"><text>カンガ</text></form>
  <form lang="pt"><text>鶏</text></form>
</lexical-unit>
```

言語コードをキーとする文字列のモデル（`MultiString`、`Record<code, string>`、`dict[str, str]`）は、これと一対一で対応します。つまり、キー1つにつき1つのエントリが、1つの `<form lang="… ">` になります。 1つのマルチテキスト内で、1つの言語につき最大1つのフォームまで許可されます。それ以外の場合、`sil-lift` は `duplicate-form-lang` という警告を出します。

XMLのエスケープ処理は、唯一、正確さが極めて重要となる部分です：

- 要素のテキスト内では、`&`、`<`, and `>` はエスケープする必要があります（`&amp;`、`&lt;`、`&gt;`）。
- 属性値では、引用符もエスケープする必要があります。

`sil-lift`の作者は、まさにこれらのルールを適用しており、`<text>`内の空白を一切変更しません。そこではインデントを追加しないのです。なぜなら、そうするとレキシカルデータが破損してしまうからです。出力と一致させるには、XMLライブラリを使用してエスケープ処理を行い、`<text>` のコンテンツはソースにあるまま、バイト単位でそのまま保持してください。

# 「LIFT」フォルダ：範囲とメディア

LIFTレキシコンは通常、_フォルダ_として構成されます。具体的には、`.lift`ファイル、1つ以上の`.lift-ranges`ファイル（サイドカーファイル）、および`audio/`と`pictures/`フォルダ内のメディアファイルで構成されます。

## 範囲

```python
lex = sil_lift.load("dictionary.lift")      # コンパニオンは自動的に追跡される

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # マージされた {id: Range} ビュー
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` は、`.lift` と追跡対象のすべてのコンパニオンをまとめて書き込みます。 `RangesFile` への編集内容は、そのファイルに保存されます。変更されていない範囲については、バイト単位でそのまま保持されます。単体での使用：

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### コンパニオンの発見

いくつかの候補が試され、その中から個別のファイルがすべて読み込まれます。

- 既存のファイルを指すヘッダー `range/@href` は、指定された通りに使用されます。
- 何も解決されない href は、`.lift` の後に続くベース名にフォールバックします。 FieldWorksは、エクスポート元マシンからの「file://C:/...」という絶対パスを記述しており、このフォールバック機能があるからこそ、ローカル環境で正常に動作するのです。
- 従来の `<name>.lift-ranges` という同階層要素は、それを参照している要素が何もなくても検出されます。

大文字小文字やUnicodeの正規化のみが異なる名前でも、依然として一致します（`Dict.LIFT` は `Dict.lift-ranges` を検出します）。ただし、1つの名前に複数のファイルが一致する場合を除きます。その場合は、いずれのファイルも読み込まれず、[`ambiguous-ranges-file`](validate.md#problem-codes) として報告されます。

`<lift-ranges>` ドキュメントとして読み取れない候補（例：エクスポートが中断されたために生成されたゼロバイトのファイルなど）は、読み込みに失敗するのではなくスキップされ、[`unreadable-ranges-file`](validate.md#problem-codes) として報告されます。 `RangesFile.load()` で直接読み込むと、代わりに例外が発生します。

`load()` に `resolve_ranges=False` を渡すと、コンパニオンの検出をスキップできます。

## メディア

```python
for ref in lex.media_refs():        # すべての<media> および<illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # 正常に解決されない参照
```

Resolutionは従来のレイアウトに従っています。相対hrefは指定された通りにチェックされ、`audio/`（発音用メディアの場合）または`pictures/`（イラストの場合）の下に配置されます。 WeSayでは、hrefを `pictures\photo with space.png` のようにスペースを入れて記述するため、バックスラッシュはスラッシュとして扱われます。リモートおよび絶対の href は検証できないため、スキップされます。

`check_media()` は、正常に解決されなかった参照のみを報告し、それぞれ 1 つの `MediaResolution` を返します：

- `status="missing"`：どのスペルで検索しても、hrefに対応するファイルが見つかりませんでした。
- `status="mismatch"`：一致したものは1つありましたが、それは大文字小文字を区別しないモード（NFC）でのみでした。`found`はディスク上のファイル名を指定します。

ファイルが見つかったにもかかわらず、不一致と報告されています。コンパニオン名は特に注意を払わずに大まかに照合されますが、メディアの href はその後そのフォルダを配信するサーバーによっても読み込まれるため、ホスト名が大文字小文字を区別する場合、ファイルが見つかりません。検証の結果、[`media-href-mismatch`](validate.md#problem-codes) と同じケースが報告されています。

## その他のフォルダ内の内容

LIFTフォルダには、sil-liftでモデル化されていないファイルが格納されていることがよくあります。例えば、`WritingSystems/` にある文字体系のLDMLや、`consent/` にあるThe Combineの話し手同意ファイルなどです。 `load()` および `save()` はこれらを変更せず、[`Lexicon.save_zip()`](lift-export-interop.md) はフォルダをパッケージ化する際、これらをそのまま引き継ぎます。

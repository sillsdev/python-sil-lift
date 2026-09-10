# 「LIFT」フォルダ：範囲とメディア

LIFTレキシコンは通常、_フォルダ_として構成されます。その中には、`.lift`ファイル、1つ以上の`.lift-ranges`ファイル（サイドカーファイル）、および`audio/` / `pictures/`フォルダ内のメディアファイルが含まれます。

## 範囲

```python
lex = sil_lift.load("dictionary.lift")      # コンパニオンは自動的に追跡される

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # マージされた {id: Range} ビュー
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` は、`.lift` と追跡対象のすべてのコンパニオンをまとめて書き込みます。 `RangesFile` への編集内容は、そのファイルに保存されます。変更されていない範囲については、バイト単位でそのまま保持されます。 単体での使用：

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### コンパニオンの発見

いくつかの候補が試され、その中から個別のファイルがすべて読み込まれます。

- 既存のファイルを指すヘッダー `range/@href` は、指定された通りに使用されます。
- 何も解決されない href は、`.lift` の後に続くベース名にフォールバックします。FieldWorks は、エクスポート元のマシンからの未参照の絶対パス `file://C:/...` を書き出しますが、このフォールバック機能によって、ローカル環境で正常に動作するようになっています。
- 従来の `<name>.lift-ranges` という同階層要素は、それを参照している要素が何もなくても検出されます。

大文字小文字やUnicodeの正規化のみが異なる名前でも一致します（`Dict.LIFT` は `Dict.lift-ranges` を検出します）。ただし、1つの名前に対して複数のファイルが一致する場合は、いずれのファイルも読み込まれず、[`ambiguous-ranges-file`](validate.md#problem-codes) として報告されます。

`load()` に `resolve_ranges=False` を渡すと、コンパニオンの検出をスキップできます。

## メディア

```python
for ref in lex.media_refs():        # すべての<media> および<illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # ファイルが存在しない参照
```

解決方法は従来のレイアウトに従います。相対的な href は指定されたままの形式でチェックされ（バックスラッシュは正規化されます — WeSay は `pictures\photo with space.png` と記述します）、`audio/`（発音用メディアの場合）または `pictures/`（イラストの場合）の下に配置されます。 リモートまたは絶対パスの href は検証できないため、スキップされます。

## その他のフォルダ内の内容

LIFTフォルダには、sil-liftがモデル化していないファイルがしばしば格納されています。たとえば、`WritingSystems/` にある文字体系の LDML ファイルや、`consent/` にある The Combine の話者同意に関する音声・画像ファイルなどです。 `load()`/`save()`はこれらをそのままにしておき、[`Lexicon.save_zip()`](lift-export-interop.md)はフォルダをパッケージ化する際、これらをそのまま引き継ぎます。

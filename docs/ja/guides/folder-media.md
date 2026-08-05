# 「LIFT」フォルダ：範囲とメディア

LIFTのレキシコンは通常、_フォルダ_として構成されます。その中には、`.lift`ファイル、1つ以上の`.lift-ranges`ファイル、および`audio/` / `pictures/`フォルダ内のメディアファイルが含まれます。

## 範囲

```python
lex = sil_lift.load("dictionary.lift")      # コンパニオンは自動的に追跡される

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # マージされた {id: Range} ビュー
lex.all_ranges()["grammatical-info"].elements
```

コンパニオンディスカバリーは実世界の状況を適切に処理します。既存のファイルを指す `range/@href` が使用されます。 FieldWorksの未参照の絶対パス `file://C:/...` のhrefは、`.lift`の隣にあるhrefのベース名にフォールバックします。また、従来の `<name>.lift-ranges` という同階層のファイルは、参照元がなくても自動的に検出されます。

`lex.save()` は、`.lift` と追跡対象のすべてのコンパニオンをまとめて書き込みます。 `RangesFile` への編集内容は、そのファイルに保存されます。変更されていない範囲については、バイト単位でそのまま保持されます。 単体での使用：

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

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

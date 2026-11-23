# C# ライブラリとの違い

sil-lift は、SIL の C# LIFT ツール群と大まかに類似しており、主に [libpalaso](https://github.com/sillsdev/libpalaso) の 2 つの部分で構成されています：

- `SIL.Lift`: パーサー、バリデータ、マイグレーター、`LiftSorter`。
- `SIL.DictionaryServices`：The Combine および WeSay で使用されている、独自の LIFT リーダー／ライターを備えた `LexEntry`/`LexSense` モデル。

sil-lift は、移植版ではなく、新たに実装されたものです。このページでは、意図的に異なる仕様となっている点をまとめています。

## 適用範囲

| 機能         | C# ライブラリ                                                 | シルリフト                                                |
| ---------- | -------------------------------------------------------- | ---------------------------------------------------- |
| LIFTのバージョン | 0.10–0.13（移行機能が組み込まれている） | **0.13のみ**；それより古いバージョンは明確なエラーで拒否されます |
| バージョンの移行   | `Migrator`（XSLTチェーン）                                     | なし。単発のアップグレードには、lift-standardに含まれるXSLTを使用してください。     |
| 検証         | RELAX NG のみ（`Validator`）                                 | RELAX NG + スキーマおよびセマンティックチェックの範囲                     |
| ストリーミング    | エントリ単位の内部解析                                              | パブリック `open_reader` / `open_writer` API              |

## APIの形状

`SIL.Lift`のパーサーはコールバック駆動型（`ILexiconMerger`）であり、解析イベントをコンシューマーにプッシュします。 sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

ストリーミングAPIは_同じ_ `Entry` 型を返すため、別途学習すべき簡略化されたモデルは存在しません。

## 往復の忠実度

最も顕著な意図的な違い。 `SIL.Lift` を使用して保存すると、ドキュメント全体が再シリアル化されます。 sil-liftの保証：

- 変更のないドキュメントは**バイト単位で同一**に保存され、
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

[フィデリティの保証](fidelity.md)をご覧ください。

## 検証

C#の`Validator`は、RELAX NGによる検証を1回実行し、最初に検出されたエラーを文字列として報告します。 sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **無効なURIはエラーではなく警告です。** C#のRELAX NGエンジンは`anyURI`データ型を強制したことがなかったため、FieldWorks (FLEx) では長年にわたり、実際のレキシコンに`file://C:/...`というhrefを記述してきました。それらのファイルを拒否すると、事実上すべてのFLExエクスポートにフラグが立てられてしまいます。
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## 規範的順序付け

`Lexicon.sort()` は、`LiftSorter` の基本ルール（エントリは大文字小文字を区別しない GUID 順、範囲および範囲要素は ID 順、ヘッダーフィールドの定義はタグ順、意味の並びはファイル順のまま、`<text>` 内の空白は一切変更しない）を踏襲していますが、3つの違いがあります：

- GUID を持たないエントリは、ID に基づいて決定論的にソートされます（`LiftSorter` は GUID が存在することを前提としています）。
- 順序付けはロケールに依存しません（大文字小文字を区別しないコードポイントに基づくものであり、.NET の不変文化ソート順序ではありません）。
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

仕様リポジトリの `canonicalizeLift.xsl` はまったく使用されていません。このXSLは、字句テキスト内の空白を削除してしまう（破壊的）うえ、生成されるIDが実行のたびに異なるからです。

## 繰り越されなかった

- WeSay特有の利便性（ダッシュボード／LIFTファイルに関する設定処理）。
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- LDMLの表記体系の解析：`WritingSystems/` ディレクトリ内のファイルは、不透明なフォルダ内容として扱われます。

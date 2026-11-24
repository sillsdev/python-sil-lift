# 大容量ファイル（ストリーミング）

`load()` はオブジェクトグラフ全体を構築します。数百MB規模の辞書の場合、ストリーミングAPIは、メモリ容量の制限内で1回につき1つのエントリを処理します。同じ `Entry` 型を返すため、一方のモード向けに書かれたコードは、もう一方のモードでも動作します。

## 読書

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # 最初に解析される（エントリより先）
    for entry in reader:              # 遅延評価される Iterator[Entry]
        ...
```

## 執筆

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:    # 例：削除済みとマークされたエントリをスキップ
            writer.write(entry)
```

注記：

- このライタの出力は、同じコンテンツに対してフルドキュメントの正規シリアライザが生成するものと完全に一致しており、この2つのモードの間で結果にずれが生じることはありません。
- ストリーミングモードでは、ソースのバイトは再利用されません。出力は常に正規化された状態になります。ルートレベルのLIFT残余（エントリ間のコメントや、`<lift>`上のスキーマ外属性）は削除されますが、エントリとヘッダーはそれぞれの残余を保持します。
- [`Lexicon.save()`](../fidelity.md#saving-an-edited-document)とは異なり、ストリーミングモードではタイムスタンプは生成されません。エントリは、すでに含まれている日付に基づいて書き込まれます。ストリーミングパスでは、ドキュメントが元の状態だった時の姿を見ることはできないため、どのエントリが変更されたかを判別することはできません。このパスで書き換えられる項目については、`entry.date_modified` を手動で設定してください。
- `open_writer` ブロック内で例外が発生した場合、ファイルは明示的に未終了の状態のまま残されます（`</lift>` による閉じ処理が行われません）。これにより、まだ書きかけの語彙集が完成しているように見えるのを防ぐことができます。

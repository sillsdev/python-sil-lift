# 大容量ファイル（ストリーミング）

`load()` はオブジェクトグラフ全体を構築します。 数百MB規模の辞書の場合、ストリーミングAPIは、制限されたメモリ内で1回に1つのエントリを処理します。エントリの型は同じ`Entry`であるため、一方のモード向けに記述されたコードは、もう一方のモードでも動作します。

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # 最初に解析される（エントリより先）
    for entry in reader:              # 遅延評価される Iterator[Entry]
        ...
```

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:    # 例：トゥームストーンを削除
            writer.write(entry)
```

注記：

- このライタの出力は、同じコンテンツに対してフルドキュメントの正規シリアライザが生成するものと完全に一致します。この2つのモードの間で結果にずれが生じることはありません。
- ストリーミングモードでは、ソースのバイトは再利用されません。出力は常に正規化された状態になります。 ルートレベルのLIFT残余（`<lift>`上のエントリ間のコメントやスキーマ外属性）は転送されません。エントリとヘッダーは、残余を含めて完全な状態で転送されます。
- `open_writer` ブロックの本体で例外が発生した場合、ファイルは明らかに未完了の状態（`</lift>` による閉じ処理が行われていない）のまま残されます。つまり、書きかけの辞書は完了しているように見えてはなりません。

# シルリフト

[LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13 用の Python ライブラリ：LIFT フォルダ（`.lift` + `.lift-ranges` + メディア参照）のロスレスな読み書き、スキーマおよびセマンティック検証、正規ソートに加え、大規模な辞書向けのストリーミング API を備えています。

**ステータス：プレリリース版、現在開発中。**

## インストール

[PyPI](https://pypi.org/project/sil-lift/)より：

```
pip install sil-lift   # ライブラリ + sil-lift コマンド
```

Python 3.11 以降が必要です。実行時の依存関係は lxml のみです。

## 30秒のツアー

語彙集を読み込み、英語の解説がないハワイ語の項目を見つけ、定義を編集して、保存します：

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # .lift-ranges のコンパニオンも追跡する

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # または lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # 編集されたエントリは再シリアル化され、再スタンプが押される。それ以外の部分はバイト単位で同一である
```

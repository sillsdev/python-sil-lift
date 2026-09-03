# シルリフト

[LIFT](https://github.com/sillsdev/lift-standard) 用の Python ライブラリ (Lexicon Interchange FormaT) 0.13: LIFTフォルダ（`.lift` + `.lift-ranges` + メディア参照）のロスレスな読み書き、スキーマおよびセマンティック検証、正規ソート機能 — 大規模なレキシコン向けのストリーミングAPIを搭載。

**ステータス：プレリリース版、現在開発中。**

## インストール

[PyPI](https://pypi.org/project/sil-lift/)より：

```
pip install sil-lift   # ライブラリ + sil-lift コマンド
```

Python 3.11 以降が必要です。 実行時の依存関係は lxml のみです。

## 30秒のツアー

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # .lift-ranges のコンパニオンも追跡する

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # または lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # 変更のないエントリはバイト単位で同一のまま。編集されたエントリは再シリアル化される
```

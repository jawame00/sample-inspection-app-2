[English version here](README_EN.md)


# 分析判定アプリ

検体データと基準値データをCSVで読み込み、基準値超過の判定・集計・履歴管理を行うデスクトップアプリです。
環境分析・品質管理の実務経験をもとに、LIMSの基本機能を想定して開発しました。

## 機能一覧

- 検体CSVと基準値CSVの読み込み
- 基準値超過の自動判定（is_exceeded）
- GUI上での明細結果表示（超過行を赤・合格行を緑で色分け）
- sample_idごとの集計表示（超過数・総項目数・総合判定）
- 判定履歴のSQLiteログ保存（実行日時・総件数・超過件数）
- sample_id・law・超過のみ でのデータ検索・絞り込み表示

## 使用技術・ライブラリ

- Python 3.x
- tkinter（GUI）
- pandas（データ処理・集計）
- sqlite3（履歴ログ保存）
- datetime（実行日時の記録）

## 必要ファイル構成
```
project/
├── app.py
├── samples.csv        # 検体データ（列：sample_id, value, law）
└── standards.csv      # 基準値データ（列：law, standard）
```

### CSVの形式例

**samples.csv**
```
sample_id,value,law
A-001,0.5,lead
A-001,1.2,arsenic
A-002,0.3,lead
```

**standards.csv**
```
law,standard
lead,1.0
arsenic,1.0
```

## 起動方法
```bash
python3 app.py
```

1. 「検体CSV」の選択ボタンでsamples.csvを選択
2. 「基準値CSV」の選択ボタンでstandards.csvを選択
3. 「判定実行」ボタンを押す
4. 明細表・集計表に結果が表示される
5. 検索エリアでsample_id・law・超過のみ での絞り込みが可能

## 今後の追加機能予定

- グラフによるデータ可視化（matplotlib）
- 検索結果のCSVエクスポート
- アラート機能（規格外データの自動検出・通知）
- SQLによる履歴データの詳細検索
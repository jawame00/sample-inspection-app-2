[English version here](README_EN.md)

# 分析判定アプリ

検体データと基準値データをCSVで読み込み、基準値超過の判定・集計・履歴管理・グラフ表示を行うデスクトップアプリです。
環境分析・品質管理の実務経験をもとに、LIMSの基本機能を想定して開発しました。

## 機能一覧

- 検体CSVと基準値CSVの読み込み
- 基準値超過の自動判定（is_exceeded）
- コントロールサンプルと通常検体の自動分離（sample_type）
- GUI上での明細結果表示（超過行を赤・合格行を緑で色分け）
- sample_idごとの集計表示（超過数・総項目数・総合判定）
- 判定履歴のSQLiteログ保存（実行日時・総件数・超過件数）
- sample_id・law・超過のみ でのデータ検索・絞り込み表示
- 月ごとの分析状況グラフ（棒グラフ）
- 超過率の月次推移グラフ（折れ線グラフ）
- 項目別超過率グラフ（横棒グラフ）
- コントロールサンプル管理図（UCL・LCL付き折れ線グラフ）

## 使用技術・ライブラリ

- Python 3.11.9
- tkinter（GUI）
- pandas（データ処理・集計）
- sqlite3（履歴ログ保存）
- matplotlib / japanize-matplotlib（グラフ表示）
- datetime（実行日時の記録）

## 必要ファイル構成
```
project/
├── app.py
├── samples.csv        # 検体データ（列：sample_id, sample_type, value, law）
└── standards.csv      # 基準値データ（列：law, standard）
```

### CSVの形式例

**samples.csv**
```
sample_id,sample_type,value,law
A001,sample,0.08,lead
A002,sample,0.12,lead
CTRL001,control,0.10,lead
```

**standards.csv**
```
law,standard
lead,0.10
arsenic,0.05
cadmium,0.03
mercury,0.005
chromium,0.20
```

## 起動方法
```bash
pip install pandas matplotlib japanize-matplotlib
python3 app.py
```

1. 「検体CSV」の選択ボタンで samples.csv を選択
2. 「基準値CSV」の選択ボタンで standards.csv を選択
3. 「判定実行」ボタンを押す
4. 明細表・集計表に結果が表示される
5. 検索エリアで絞り込み・各グラフボタンでグラフを表示

## グラフ機能

| ボタン | 内容 | データソース |
|---|---|---|
| 月次グラフ | 月ごとの実行回数・平均件数 | SQLiteログ |
| 超過率トレンド | 超過率の月次推移 | SQLiteログ |
| 項目別超過率 | 項目ごとの超過割合 | 判定結果 |
| 管理図 | コントロールサンプルのUCL・LCL管理 | 判定結果 |

## 今後の追加機能予定

- 検索結果のCSVエクスポート
- アラート機能（規格外データの自動検出・通知）
- SQLによる履歴データの詳細検索
- Webアプリ化（Streamlit）
import tkinter as tk  # Python標準GUIライブラリ tkinter を tk という名前で使用する
from tkinter import filedialog, messagebox  # ファイル選択ダイアログとメッセージ表示機能を読み込む
from tkinter import ttk # Treeview（表）を読み込む
import pandas as pd  # データ処理ライブラリ pandas を pd という名前で使用する
import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect('inspection.db')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        実行日時 TEXT,総件数 INTEGER, 超過件数 INTEGER)
    """)
    conn.commit()

def save_log(total, exceeded):
    conn = sqlite3.connect("inspection.db")
    conn.execute(
        "INSERT INTO logs (実行日時, 総件数, 超過件数) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, exceeded)
    )
    conn.commit()
    conn.close()


def process_csv(samples_path, standards_path, output_path="result.csv"):  
    # CSVデータを読み込み、基準値と比較して結果CSVを作成する関数

    samples = pd.read_csv(samples_path)  
    # 検体データのCSVファイルを読み込んでDataFrameに変換

    standards = pd.read_csv(standards_path)  
    # 基準値データのCSVファイルを読み込んでDataFrameに変換

    merged = samples.merge(standards, on="law", how="left")  
    # samples と standards を「law」という列をキーに結合する
    # how="left" は samples を基準に結合する（左外部結合）

    merged["is_exceeded"] = merged["value"] > merged["standard"]  
    # 測定値(value)が基準値(standard)より大きいかを判定
    # True / False の結果を新しい列 "is_exceeded" に保存

    merged.to_csv(output_path, index=False)  
    # 結合・判定したデータをCSVファイルとして保存
    # index=False は行番号（インデックス）を出力しない設定

    summary = merged.groupby("sample_id").agg(
        超過数=("is_exceeded", "sum"),
        総項目数=("is_exceeded", "count")
        ).reset_index()
    summary["総合判定"] = summary["超過数"].apply(
        lambda x: "不合格" if x > 0 else "合格"
        )

    return merged, summary
    # process_csv()に戻り値を設定
    # mergedを外に出す


def select_samples():  
    # 検体CSVファイルを選択するための関数

    path = filedialog.askopenfilename(  
        title="検体CSVを選択",  # ダイアログのタイトル
        filetypes=[("CSV files", "*.csv")]  # CSVファイルのみ表示
    )

    samples_var.set(path)  
    # 選択されたファイルパスを samples_var に保存
    # Entryボックスにも表示される


def select_standards():  
    # 基準値CSVファイルを選択する関数

    path = filedialog.askopenfilename(
        title="基準値CSVを選択",  # ダイアログタイトル
        filetypes=[("CSV files", "*.csv")]  # CSVファイルのみ表示
    )

    standards_var.set(path)  
    # 選択したファイルパスを standards_var に保存


current_result = None  # 検索用にresultを保持するグローバル変数

def run_process():  
    # 判定処理を実行する関数（ボタンを押すと呼ばれる）

    samples_path = samples_var.get()  
    # GUI入力欄から検体CSVのパスを取得

    standards_path = standards_var.get()  
    # GUI入力欄から基準値CSVのパスを取得


    if not samples_path or not standards_path:  
        # どちらかのCSVが選択されていない場合

        messagebox.showerror("エラー", "CSVを両方選択してください")  
        # エラーメッセージを表示

        return  
        # 処理を終了


    try:  
        # エラー発生時に処理が止まらないよう例外処理を開始

        result, summary = process_csv(samples_path, standards_path)  
        # CSV処理関数を実行して、resultに渡す。

        global current_result
        current_result = result  # 検索ボタンが押されたときのために保存しておく

        save_log(len(result),int(result['is_exceeded'].sum()))
        # 総件数と超過件数をDBに保存

        messagebox.showinfo("完了", "判定が完了しました")  
        # 処理完了メッセージを表示

        show_result(result)
        # 明細表（既存）

        show_summary(summary)
        # 集計表


    except Exception as e:  
        # エラーが発生した場合

        messagebox.showerror("エラー", str(e))  
        # エラー内容を画面に表示


def show_result(df):
    # 既存の表があれば一度消す（再実行時に重複しないように）
    for widget in frame_result.winfo_children():
        widget.destroy()

    # 列名を取得してTreeviewを作る
    columns = list(df.columns)
    tree = ttk.Treeview(frame_result, columns=columns, show="headings", height=10)

    # 各列のヘッダーと幅を設定する
    for col in columns:
        tree.heading(col, text=col)   # ヘッダーに列名を表示
        tree.column(col, width=120)   # 各列の幅を120pxに設定

    # データを1行ずつ表に入れる
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

    # スクロールバーを付ける
    scrollbar = ttk.Scrollbar(frame_result, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


def search():
    # 検索条件を取得して result を絞り込む関数
    if current_result is None:
        messagebox.showerror("エラー", "先に判定実行してください")
        return

    df = current_result.copy()  # 元データを壊さないようにコピーする

    # sample_id で絞り込み（入力があれば）
    sid = search_sample_var.get().strip()
    if sid:
        df = df[df["sample_id"].astype(str).str.contains(sid)]

    # law で絞り込み（入力があれば）
    law = search_law_var.get().strip()
    if law:
        df = df[df["law"].astype(str).str.contains(law)]

    # 超過のみ表示（チェックが入っていれば）
    if exceeded_var.get():
        df = df[df["is_exceeded"] == True]

    show_search(df)  # 絞り込んだ結果を表示する


def show_search(df):
    # 検索結果をTreeviewに表示する関数
    for widget in frame_search.winfo_children():
        widget.destroy()

    columns = list(df.columns)
    tree = ttk.Treeview(frame_search, columns=columns, show="headings", height=6)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    for _, row in df.iterrows():
        tag = "ng" if row["is_exceeded"] else "ok"
        tree.insert("", "end", values=list(row), tags=(tag,))

    tree.tag_configure("ng", background="#FFCCCC")
    tree.tag_configure("ok", background="#CCFFCC")

    scrollbar = ttk.Scrollbar(frame_search, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


def show_summary(df):
    for widget in frame_summary.winfo_children():
        widget.destroy()

    columns = list(df.columns)
    tree = ttk.Treeview(frame_summary, columns=columns, show="headings", height=6)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    for _, row in df.iterrows():
        # 不合格行を赤く色づけする
        tag = "ng" if row["総合判定"] == "不合格" else "ok"
        tree.insert("", "end", values=list(row), tags=(tag,))

    tree.tag_configure("ng", background="#FFCCCC")
    tree.tag_configure("ok", background="#CCFFCC")

    scrollbar = ttk.Scrollbar(frame_summary, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


init_db()
# アプリ起動時にDBとテーブルを準備する

root = tk.Tk()  
# tkinterアプリのメインウィンドウを作成

root.title("分析判定アプリ（CSV版）")  
# ウィンドウのタイトルを設定



samples_var = tk.StringVar()  
# GUI入力値を保存するための文字列変数（検体CSV）

standards_var = tk.StringVar()  
# GUI入力値を保存するための文字列変数（基準値CSV）



tk.Label(root, text="検体CSV").grid(row=0, column=0, padx=5, pady=5)  
# 「検体CSV」というラベルを配置


tk.Entry(root, textvariable=samples_var, width=40).grid(row=0, column=1)  
# CSVパスを表示・入力するテキストボックス


tk.Button(root, text="選択", command=select_samples).grid(row=0, column=2)  
# ファイル選択ボタン
# 押すと select_samples() が実行される



tk.Label(root, text="基準値CSV").grid(row=1, column=0, padx=5, pady=5)  
# 「基準値CSV」というラベル


tk.Entry(root, textvariable=standards_var, width=40).grid(row=1, column=1)  
# 基準値CSVパス入力欄


tk.Button(root, text="選択", command=select_standards).grid(row=1, column=2)  
# 基準値CSVを選択するボタン



tk.Button(root, text="判定実行", command=run_process, width=20).grid(row=2, column=1, pady=10)  
# 判定処理を実行するボタン
# 押すと run_process() が呼ばれる


# 結果表示エリアをウィンドウに追加
frame_result = tk.Frame(root)
frame_result.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
frame_summary = tk.Frame(root)
frame_summary.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

# 検索条件入力エリア
frame_search_input = tk.Frame(root)
frame_search_input.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="w")

search_sample_var = tk.StringVar()
search_law_var = tk.StringVar()
exceeded_var = tk.BooleanVar()

tk.Label(frame_search_input, text="sample_id:").pack(side="left")
tk.Entry(frame_search_input, textvariable=search_sample_var, width=12).pack(side="left")
tk.Label(frame_search_input, text="  law:").pack(side="left")
tk.Entry(frame_search_input, textvariable=search_law_var, width=12).pack(side="left")
tk.Checkbutton(frame_search_input, text="超過のみ", variable=exceeded_var).pack(side="left")
tk.Button(frame_search_input, text="検索", command=search).pack(side="left", padx=8)

# 検索結果表示エリア
frame_search = tk.Frame(root)
frame_search.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.mainloop()  
# GUIアプリを起動し、ユーザー操作を待ち続ける（イベントループ）
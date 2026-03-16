import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect("inspection.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            実行日時 TEXT, 総件数 INTEGER, 超過件数 INTEGER)
    """)
    conn.commit()
    conn.close()


def save_log(total, exceeded):
    conn = sqlite3.connect("inspection.db")
    conn.execute(
        "INSERT INTO logs (実行日時, 総件数, 超過件数) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, exceeded)
    )
    conn.commit()
    conn.close()


def process_csv(samples_path, standards_path, output_path="result.csv"):
    samples = pd.read_csv(samples_path)
    standards = pd.read_csv(standards_path)

    # law をキーに左外部結合
    merged = samples.merge(standards, on="law", how="left")

    # 測定値が基準値を超えているか判定
    merged["is_exceeded"] = merged["value"] > merged["standard"]
    merged.to_csv(output_path, index=False)

    # sample_id ごとに超過数・総項目数を集計
    summary = merged.groupby("sample_id").agg(
        超過数=("is_exceeded", "sum"),
        総項目数=("is_exceeded", "count")
    ).reset_index()
    summary["総合判定"] = summary["超過数"].apply(
        lambda x: "不合格" if x > 0 else "合格"
    )

    return merged, summary


def select_samples():
    path = filedialog.askopenfilename(
        title="検体CSVを選択",
        filetypes=[("CSV files", "*.csv")]
    )
    samples_var.set(path)


def select_standards():
    path = filedialog.askopenfilename(
        title="基準値CSVを選択",
        filetypes=[("CSV files", "*.csv")]
    )
    standards_var.set(path)


# 検索ボタン押下時に result にアクセスできるようグローバルで保持
current_result = None


def run_process():
    samples_path = samples_var.get()
    standards_path = standards_var.get()

    if not samples_path or not standards_path:
        messagebox.showerror("エラー", "CSVを両方選択してください")
        return

    try:
        result, summary = process_csv(samples_path, standards_path)

        global current_result
        current_result = result

        # commitの前にmessageboxを挟まないよう先に保存する
        save_log(len(result), int(result["is_exceeded"].sum()))

        messagebox.showinfo("完了", "判定が完了しました")
        show_result(result)
        show_summary(summary)

    except Exception as e:
        messagebox.showerror("エラー", str(e))


def _build_tree(frame, df, height):
    """Treeview と縦スクロールバーを frame 内に構築する共通関数"""
    for widget in frame.winfo_children():
        widget.destroy()

    columns = list(df.columns)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    tree.tag_configure("ng", background="#FFCCCC")
    tree.tag_configure("ok", background="#CCFFCC")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return tree


def show_result(df):
    tree = _build_tree(frame_result, df, height=10)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))


def show_summary(df):
    tree = _build_tree(frame_summary, df, height=6)
    for _, row in df.iterrows():
        tag = "ng" if row["総合判定"] == "不合格" else "ok"
        tree.insert("", "end", values=list(row), tags=(tag,))


def show_search(df):
    tree = _build_tree(frame_search, df, height=6)
    for _, row in df.iterrows():
        tag = "ng" if row["is_exceeded"] else "ok"
        tree.insert("", "end", values=list(row), tags=(tag,))


def search():
    if current_result is None:
        messagebox.showerror("エラー", "先に判定実行してください")
        return

    # 元データを壊さないようにコピーしてから絞り込む
    df = current_result.copy()

    sid = search_sample_var.get().strip()
    if sid:
        df = df[df["sample_id"].astype(str).str.contains(sid)]

    law = search_law_var.get().strip()
    if law:
        df = df[df["law"].astype(str).str.contains(law)]

    if exceeded_var.get():
        df = df[df["is_exceeded"] == True]

    show_search(df)


# アプリ起動時にDBとテーブルを準備
init_db()

root = tk.Tk()
root.title("分析判定アプリ（CSV版）")

samples_var = tk.StringVar()
standards_var = tk.StringVar()

tk.Label(root, text="検体CSV").grid(row=0, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=samples_var, width=40).grid(row=0, column=1)
tk.Button(root, text="選択", command=select_samples).grid(row=0, column=2)

tk.Label(root, text="基準値CSV").grid(row=1, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=standards_var, width=40).grid(row=1, column=1)
tk.Button(root, text="選択", command=select_standards).grid(row=1, column=2)

tk.Button(root, text="判定実行", command=run_process, width=20).grid(row=2, column=1, pady=10)

frame_result = tk.Frame(root)
frame_result.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

frame_summary = tk.Frame(root)
frame_summary.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

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

frame_search = tk.Frame(root)
frame_search.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.mainloop()
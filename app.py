import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import japanize_matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

    # 通常検体とコントロールサンプルを分離する
    df_sample = merged[merged["sample_type"] == "sample"]
    df_control = merged[merged["sample_type"] == "control"]

    # 通常検体のみで集計する
    summary = df_sample.groupby("sample_id").agg(
        超過数=("is_exceeded", "sum"),
        総項目数=("is_exceeded", "count")
    ).reset_index()
    summary["総合判定"] = summary["超過数"].apply(
        lambda x: "不合格" if x > 0 else "合格"
    )

    return merged, summary, df_control

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


current_result = None   # 検索ボタン押下時に result にアクセスできるようグローバルで保持
current_control = None  # 管理図用にコントロールサンプルを保持


def run_process():
    samples_path = samples_var.get()
    standards_path = standards_var.get()

    if not samples_path or not standards_path:
        messagebox.showerror("エラー", "CSVを両方選択してください")
        return

    try:
        result, summary, df_control = process_csv(samples_path, standards_path)

        global current_result
        current_result = result

        global current_control
        current_control = df_control

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


def show_monthly_chart():
    # logsテーブルから月ごとの件数を集計して棒グラフを表示する
    conn = sqlite3.connect("inspection.db")
    df_log = pd.read_sql("SELECT * FROM logs", conn)
    conn.close()

    if df_log.empty:
        messagebox.showinfo("情報", "ログデータがありません。先に判定実行してください。")
        return

    # 実行日時から「年月」を抽出して集計
    df_log["年月"] = pd.to_datetime(df_log["実行日時"]).dt.strftime("%Y-%m")
    monthly = df_log.groupby("年月").agg(
        実行回数=("総件数", "count"),    
        平均総件数=("総件数", "mean"),
        平均超過件数=("超過件数", "mean")
    ).reset_index()

    # グラフウィンドウを作成
    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(monthly))
    width = 0.25

    ax.bar([i - width for i in x], monthly["実行回数"],
       width=width, label="実行回数", color="#7F77DD")
    ax.bar([i for i in x], monthly["平均総件数"],
       width=width, label="平均総件数", color="#5DCAA5")
    ax.bar([i + width for i in x], monthly["平均超過件数"],
       width=width, label="平均超過件数", color="#F0997B")

    ax.set_xticks(list(x))
    ax.set_xticklabels(monthly["年月"], rotation=45)
    ax.set_title("月ごとの分析状況")
    ax.set_ylabel("件数・回数")
    ax.legend()
    plt.tight_layout()

    # 新しいウィンドウに表示
    chart_window = tk.Toplevel(root)
    chart_window.title("月次分析グラフ")
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def show_trend_chart():
    # 超過率の月次推移を折れ線グラフで表示する
    conn = sqlite3.connect("inspection.db")
    df_log = pd.read_sql("SELECT * FROM logs", conn)
    conn.close()

    if df_log.empty:
        messagebox.showinfo("情報", "ログデータがありません。先に判定実行してください。")
        return

    # 月ごとに超過率を計算する
    df_log["年月"] = pd.to_datetime(df_log["実行日時"]).dt.strftime("%Y-%m")
    monthly = df_log.groupby("年月").agg(
        総件数=("総件数", "sum"),
        超過件数=("超過件数", "sum")
    ).reset_index()

    # 超過率（%）を計算する
    monthly["超過率"] = (monthly["超過件数"] / monthly["総件数"] * 100).round(1)

    # グラフを作成する
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(monthly["年月"], monthly["超過率"],
            marker="o", color="#D85A30", linewidth=2, label="超過率(%)")

    # 警告ラインを引く（20%を超えたら要注意）
    ax.axhline(y=20, color="#FA7517", linestyle="--",
               linewidth=1, label="注意ライン(20%)")

    ax.set_title("超過率の月次推移")
    ax.set_ylabel("超過率(%)")
    ax.set_ylim(0, 100)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    chart_window = tk.Toplevel(root)
    chart_window.title("超過率トレンドグラフ")
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def show_item_chart():
    # 項目別超過割合を横棒グラフで表示する
    if current_result is None:
        messagebox.showinfo("情報", "先に判定実行してください。")
        return

    # 項目ごとに総件数と超過件数を集計する
    df = current_result.groupby("law").agg(
        総件数=("is_exceeded", "count"),
        超過件数=("is_exceeded", "sum")
    ).reset_index()

    # 超過率を計算する
    df["超過率"] = (df["超過件数"] / df["総件数"] * 100).round(1)
    df = df.sort_values("超過率", ascending=True)

    # 横棒グラフを作成する
    fig, ax = plt.subplots(figsize=(8, max(3, len(df) * 0.6)))

    bars = ax.barh(df["law"], df["超過率"],
                   color="#7F77DD", alpha=0.8)

    # 各バーに超過率の数値を表示する
    for bar, val in zip(bars, df["超過率"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val}%", va="center", fontsize=10)

    ax.set_title("項目別超過率")
    ax.set_xlabel("超過率(%)")
    ax.set_xlim(0, 110)
    plt.tight_layout()

    chart_window = tk.Toplevel(root)
    chart_window.title("項目別超過率グラフ")
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def show_control_chart():
    # コントロールサンプルの管理図を表示する
    if current_control is None or current_control.empty:
        messagebox.showinfo("情報", "先に判定実行してください。")
        return

    laws = current_control["law"].unique()
    fig, axes = plt.subplots(len(laws), 1,
                             figsize=(8, max(4, len(laws) * 2)))

    # 項目が1つの場合はaxesをリストにする
    if len(laws) == 1:
        axes = [axes]

    for ax, law in zip(axes, laws):
        df = current_control[current_control["law"] == law]
        standard = df["standard"].iloc[0]

        # 管理限界線を計算する（基準値±20%）
        ucl = standard * 1.20  # 上方管理限界
        lcl = standard * 0.80  # 下方管理限界

        ax.plot(df.index, df["value"],
                marker="o", color="#7F77DD",
                linewidth=2, label="測定値")

        # 基準値ライン
        ax.axhline(y=standard, color="#1D9E75",
                   linestyle="-", linewidth=1.5, label=f"基準値({standard})")

        # 上方管理限界ライン
        ax.axhline(y=ucl, color="#E24B4A",
                   linestyle="--", linewidth=1, label=f"UCL({ucl:.3f})")

        # 下方管理限界ライン
        ax.axhline(y=lcl, color="#BA7517",
                   linestyle="--", linewidth=1, label=f"LCL({lcl:.3f})")

        # 管理限界を外れた点を赤くする
        for idx, row in df.iterrows():
            if row["value"] > ucl or row["value"] < lcl:
                ax.plot(idx, row["value"],
                        marker="o", color="#E24B4A", markersize=10)

        ax.set_title(f"{law} 管理図")
        ax.set_ylabel("測定値")
        ax.legend(fontsize=8)

    plt.tight_layout()

    chart_window = tk.Toplevel(root)
    chart_window.title("コントロールサンプル管理図")
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

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
tk.Button(frame_search_input, text="月次グラフ", command=show_monthly_chart).pack(side="left", padx=8)
tk.Button(frame_search_input, text="超過率トレンド", command=show_trend_chart).pack(side="left", padx=8)
tk.Button(frame_search_input, text="項目別超過率", command=show_item_chart).pack(side="left", padx=8)
tk.Button(frame_search_input, text="管理図", command=show_control_chart).pack(side="left", padx=8)

frame_search = tk.Frame(root)
frame_search.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

root.mainloop()
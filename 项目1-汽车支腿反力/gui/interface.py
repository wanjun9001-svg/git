import csv
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox

from calculation.crane import calculate as calculate_crane


INPUT_FIELDS = [
    ("G3", "汽车吊吊臂自重G3 (t)"),
    ("E", "吊臂重心至回转中心E (m)"),
    ("G0", "汽车吊自重G0 (t)"),
    ("G1", "起吊构件重量G1 (t)"),
    ("G2", "配重G2 (t)"),
    ("L1", "起吊半径L1 (m)"),
    ("A", "支腿纵距A (m)"),
    ("B", "支腿横距B (m)"),
    ("C", "配重距离C (m)"),
    ("g", "重力加速度g (m/s²)"),
    ("D", "回转中心至后支腿距离D (m)"),
    ("a", "路基箱长a (m)"),
    ("b", "路基箱宽b (m)"),
]

OUTPUT_FIELDS = [
    ("β", "水平角β (°)"),
    ("cosβ", "cosβ"),
    ("sinβ", "sinβ"),
    ("F", "总竖向力F (kN)"),
    ("M", "总弯矩M (kN·m)"),
    ("Mx", "X轴弯矩Mx (kN·m)"),
    ("My", "Y轴弯矩My (kN·m)"),
    ("N1", "支腿1反力N1 (kN)"),
    ("N2", "支腿2反力N2 (kN)"),
    ("N3", "支腿3反力N3 (kN)"),
    ("N4", "支腿4反力N4 (kN)"),
    ("S", "路基箱面积S (m²)"),
    ("P", "最大地面压强P (kPa)"),
    ("N_max", "最大支腿反力Nmax (kN)"),
]


class App:
    def __init__(self) -> None:
        self.entries: dict[str, tk.Entry] = {}
        self.outputs: dict[str, tk.Label] = {}
        self.history: list[dict[str, float | str]] = []
        self.history_box: tk.Listbox | None = None

        self.root = tk.Tk()
        self.root.title("支腿反力验算系统 Pro")
        self.root.geometry("900x800")

        self._build_menu()
        self._build_layout()

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="导出记录", command=self.export_csv)
        file_menu.add_command(label="退出", command=self.root.quit)
        menu.add_cascade(label="文件", menu=file_menu)

        calc_menu = tk.Menu(menu, tearoff=0)
        calc_menu.add_command(label="计算", command=self.calculate)
        calc_menu.add_command(label="清空输入", command=self.clear_inputs)
        menu.add_cascade(label="计算", menu=calc_menu)

        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        main = tk.Frame(self.root, padx=10, pady=10)
        main.pack(fill=tk.BOTH, expand=True)

        input_frame = tk.LabelFrame(main, text="输入参数")
        input_frame.pack(fill=tk.X, pady=5)

        for i, (k, t) in enumerate(INPUT_FIELDS):
            tk.Label(input_frame, text=t, width=35, anchor="w").grid(row=i, column=0, sticky="w")
            e = tk.Entry(input_frame)
            e.grid(row=i, column=1, sticky="ew")
            self.entries[k] = e

        input_frame.columnconfigure(1, weight=1)

        output_frame = tk.LabelFrame(main, text="计算结果")
        output_frame.pack(fill=tk.X, pady=5)

        for i, (k, t) in enumerate(OUTPUT_FIELDS):
            tk.Label(output_frame, text=t, width=25, anchor="w").grid(row=i, column=0, sticky="w")
            l = tk.Label(output_frame, text="", width=20, relief=tk.SUNKEN)
            l.grid(row=i, column=1, sticky="w")
            self.outputs[k] = l

        hist_frame = tk.LabelFrame(main, text="计算记录（最近20条）")
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.history_box = tk.Listbox(hist_frame)
        self.history_box.pack(fill=tk.BOTH, expand=True)

        btn = tk.Frame(main)
        btn.pack(pady=10)

        tk.Button(btn, text="计算", width=15, command=self.calculate).grid(row=0, column=0, padx=10)
        tk.Button(btn, text="清空", width=15, command=self.clear_inputs).grid(row=0, column=1, padx=10)
        tk.Button(btn, text="导出Excel(CSV)", width=18, command=self.export_csv).grid(row=0, column=2, padx=10)

    def _read_inputs(self) -> dict[str, float]:
        data: dict[str, float] = {}
        for k, _ in INPUT_FIELDS:
            v = self.entries[k].get().strip()
            if v == "":
                raise ValueError(f"请输入 {k}")
            data[k] = float(v)
        return data

    def calculate(self) -> None:
        try:
            data = self._read_inputs()
            result = calculate_crane(data)

            for k, _ in OUTPUT_FIELDS:
                self.outputs[k].config(text=f"{result[k]:.2f}")

            record = {"time": datetime.now().strftime("%H:%M:%S"), **data, **result}
            self.history.append(record)
            self.refresh_history()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def clear_inputs(self) -> None:
        for e in self.entries.values():
            e.delete(0, tk.END)

    def refresh_history(self) -> None:
        if not self.history_box:
            return
        self.history_box.delete(0, tk.END)
        for h in self.history[-20:]:
            f = float(h["F"])
            n_max = float(h["N_max"])
            t = str(h["time"])
            self.history_box.insert(tk.END, f"{t} | F={f:.1f}kN | Nmax={n_max:.1f}kN")

    def export_csv(self) -> None:
        if not self.history:
            messagebox.showwarning("提示", "没有数据可导出")
            return

        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
            writer.writeheader()
            writer.writerows(self.history)

        messagebox.showinfo("成功", "导出完成")


def run() -> None:
    app = App()
    app.root.mainloop()


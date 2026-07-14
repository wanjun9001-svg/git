import math
import tkinter as tk
from tkinter import messagebox, filedialog
import csv
from datetime import datetime

# ===================== 输入 / 输出定义 =====================
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

# ===================== 数据存储 =====================
entries = {}
outputs = {}
history = []

# ===================== 计算核心 =====================
def calculate():
    try:
        data = {}
        for k, _ in INPUT_FIELDS:
            v = entries[k].get().strip()
            if v == "":
                raise ValueError(f"请输入 {k}")
            data[k] = float(v)
       
        if data["D"] == 0:
            raise ValueError("回转中心至后支腿距离 D 不能为0")

        β = math.degrees(math.atan(data["B"] / (2 * data["D"])))

        β_rad = math.radians(β)

        cosβ = math.cos(β_rad)
        sinβ = math.sin(β_rad)

        F = (data["G0"] + data["G1"] + data["G2"] + data["G3"]) * data["g"]
        M = (data["G1"] * data["L1"] - data["G2"] * data["C"] + data["G3"] * data["E"]) * data["g"]

        Mx = M * cosβ
        My = M * sinβ

        N1 = data["D"] * F / (2 * data["A"]) - Mx / (2 * data["A"]) + My / (2 * data["B"])
        N2 = (data["A"] - data["D"]) * F / (2 * data["A"]) + Mx / (2 * data["A"]) + My / (2 * data["B"])
        N3 = data["D"] * F / (2 * data["A"]) - Mx / (2 * data["A"]) - My / (2 * data["B"])
        N4 = (data["A"] - data["D"]) * F / (2 * data["A"]) + Mx / (2 * data["A"]) - My / (2 * data["B"])

        N_max = max(N1, N2, N3, N4)
        S = data["a"] * data["b"]
        P = N_max / S if S != 0 else 0

        result = {
             "β": β,
            "cosβ": cosβ,
            "sinβ": sinβ,
            "F": F,
            "M": M,
            "Mx": Mx,
            "My": My,
            "N1": N1,
            "N2": N2,
            "N3": N3,
            "N4": N4,
            "S": S,
            "P": P,
            "N_max": N_max,
        }

        # 输出
        for k, _ in OUTPUT_FIELDS:
            outputs[k].config(text=f"{result[k]:.2f}")

        # 记录历史
        record = {
            "time": datetime.now().strftime("%H:%M:%S"),
            **data,
            **result
        }
        history.append(record)
        refresh_history()

    except Exception as e:
        messagebox.showerror("错误", str(e))


def clear_inputs():
    for e in entries.values():
        e.delete(0, tk.END)


def refresh_history():
    history_box.delete(0, tk.END)
    for h in history[-20:]:
        history_box.insert(
            tk.END,
            f"{h['time']} | F={h['F']:.1f}kN | Nmax={h['N_max']:.1f}kN"
        )


def export_csv():
    if not history:
        messagebox.showwarning("提示", "没有数据可导出")
        return

    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if not file:
        return

    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)

    messagebox.showinfo("成功", "导出完成")


# ===================== GUI =====================
def build_gui():
    global history_box

    root = tk.Tk()
    root.title("支腿反力验算系统 Pro")
    root.geometry("900x800")

    # ===== 菜单 =====
    menu = tk.Menu(root)

    file_menu = tk.Menu(menu, tearoff=0)
    file_menu.add_command(label="导出记录", command=export_csv)
    file_menu.add_command(label="退出", command=root.quit)
    menu.add_cascade(label="文件", menu=file_menu)

    calc_menu = tk.Menu(menu, tearoff=0)
    calc_menu.add_command(label="计算", command=calculate)
    calc_menu.add_command(label="清空输入", command=clear_inputs)
    menu.add_cascade(label="计算", menu=calc_menu)

    root.config(menu=menu)

    # ===== 主框架 =====
    main = tk.Frame(root, padx=10, pady=10)
    main.pack(fill=tk.BOTH, expand=True)

    # ===== 输入 =====
    input_frame = tk.LabelFrame(main, text="输入参数")
    input_frame.pack(fill=tk.X, pady=5)

    for i, (k, t) in enumerate(INPUT_FIELDS):
        tk.Label(input_frame, text=t, width=35, anchor="w").grid(row=i, column=0, sticky="w")
        e = tk.Entry(input_frame)
        e.grid(row=i, column=1, sticky="ew")
        entries[k] = e

    input_frame.columnconfigure(1, weight=1)

    # ===== 输出 =====
    output_frame = tk.LabelFrame(main, text="计算结果")
    output_frame.pack(fill=tk.X, pady=5)

    for i, (k, t) in enumerate(OUTPUT_FIELDS):
        tk.Label(output_frame, text=t, width=25, anchor="w").grid(row=i, column=0, sticky="w")
        l = tk.Label(output_frame, text="", width=20, relief=tk.SUNKEN)
        l.grid(row=i, column=1, sticky="w")
        outputs[k] = l

    # ===== 历史 =====
    hist_frame = tk.LabelFrame(main, text="计算记录（最近20条）")
    hist_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    history_box = tk.Listbox(hist_frame)
    history_box.pack(fill=tk.BOTH, expand=True)

    # ===== 按钮 =====
    btn = tk.Frame(main)
    btn.pack(pady=10)

    tk.Button(btn, text="计算", width=15, command=calculate).grid(row=0, column=0, padx=10)
    tk.Button(btn, text="清空", width=15, command=clear_inputs).grid(row=0, column=1, padx=10)
    tk.Button(btn, text="导出Excel(CSV)", width=18, command=export_csv).grid(row=0, column=2, padx=10)

    return root


if __name__ == "__main__":
    app = build_gui()
    app.mainloop()
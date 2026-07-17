from __future__ import annotations

from copy import deepcopy
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import struct
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _workspace_root() -> Path:
    return _project_root().parent


def _reexec_with_venv() -> None:
    script = Path(__file__).resolve()
    venv_scripts = _workspace_root() / ".venv" / "Scripts"

    venv_python = venv_scripts / "python.exe"
    venv_pythonw = venv_scripts / "pythonw.exe"

    if not venv_python.exists() and not venv_pythonw.exists():
        return

    current = Path(sys.executable).resolve()
    if (venv_python.exists() and current == venv_python.resolve()) or (
        venv_pythonw.exists() and current == venv_pythonw.resolve()
    ):
        return

    target = venv_pythonw if venv_pythonw.exists() else venv_python
    subprocess.Popen([str(target), str(script), *sys.argv[1:]], cwd=str(_project_root()))
    raise SystemExit(0)


def _ensure_project_root_on_path() -> None:
    root = str(_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


_reexec_with_venv()
_ensure_project_root_on_path()

from calculation.crane import calculate_report


PRIMARY_BG = "#eef3f7"
PANEL_BG = "#ffffff"
TITLE_BG = "#1f4e79"
TITLE_FG = "#ffffff"
ACCENT_BG = "#2f75b5"
ACCENT_ACTIVE_BG = "#1f5d96"
BORDER_COLOR = "#9fb3c8"
TEXT_MUTED = "#5b6b7a"


INPUT_FIELDS = [
    ("G3", "汽车吊吊臂自重 G3", "t"),
    ("E", "吊臂重心至回转中心 E", "m"),
    ("G0", "汽车吊自重（扣除吊臂重量） G0", "t"),
    ("G1", "起吊构件最大重量 G1", "t"),
    ("G2", "配重 G2", "t"),
    ("L1", "起吊作业半径 L1", "m"),
    ("A", "支腿纵距 A", "m"),
    ("B", "支腿横距 B", "m"),
    ("C", "配重至回转中心距离 C", "m"),
    ("g", "重力加速度 g", "m/s²"),
    ("D", "回转中心至后支腿距离 D", "m"),
    ("a", "路基箱长 a", "m"),
    ("b", "路基箱宽 b", "m"),
]

MODEL_FIELD = ("crane_model", "汽车吊型号", "t")
ALL_INPUT_FIELDS = [MODEL_FIELD, *INPUT_FIELDS]

INPUT_GROUPS = [
    ("基本信息", ["crane_model"]),
    ("荷载参数", ["G0", "G1", "G2", "G3", "g"]),
    ("布置参数", ["E", "L1", "A", "B", "C", "D"]),
    ("基础参数", ["a", "b"]),
]

DEFAULT_INPUTS = {
    "crane_model": "300",
    "G3": "17.79",
    "E": "9",
    "G0": "52.45",
    "G1": "18.6",
    "G2": "76",
    "L1": "20",
    "A": "9.19",
    "B": "8.3",
    "C": "4.3",
    "D": "4.15",
    "g": "9.81",
}

OUTPUT_FIELDS = [
    ("β", "水平角 β", "°"),
    ("cosβ", "cosβ", "-"),
    ("sinβ", "sinβ", "-"),
    ("F", "总竖向力 F", "kN"),
    ("M", "总弯矩 M", "kN·m"),
    ("Mx", "X 轴弯矩 Mx", "kN·m"),
    ("My", "Y 轴弯矩 My", "kN·m"),
    ("N1", "支腿 1 反力 N1", "kN"),
    ("N2", "支腿 2 反力 N2", "kN"),
    ("N3", "支腿 3 反力 N3", "kN"),
    ("N4", "支腿 4 反力 N4", "kN"),
    ("S", "路基箱面积 S", "m²"),
    ("P", "最大地面压强 P", "kPa"),
    ("N_max", "最大支腿反力 Nmax", "kN"),
]


class App:
    def __init__(self) -> None:
        self.entries: dict[str, tk.Entry] = {}
        self.history: list[dict[str, object]] = []
        self.history_window: tk.Toplevel | None = None
        self.history_listbox: tk.Listbox | None = None
        self.last_report: dict[str, object] | None = None
        self.result_tree: ttk.Treeview | None = None
        self.steps_text: tk.Text | None = None
        self.diagram_photo: tk.PhotoImage | None = None
        self.diagram_label: tk.Label | None = None
        self.diagram_container: tk.Frame | None = None
        self.diagram_viewer: tk.Toplevel | None = None
        self.diagram_viewer_canvas: tk.Canvas | None = None
        self.diagram_viewer_base: tk.PhotoImage | None = None
        self.diagram_viewer_photo: tk.PhotoImage | None = None
        self.diagram_viewer_image_id: int | None = None
        self.diagram_viewer_scale: tuple[int, int] = (1, 1)

        self.root = tk.Tk()
        self.root.title("汽车吊支腿反力自动生成计算书")
        self.root.geometry("1400x860")
        self.root.minsize(1180, 720)
        self.root.configure(bg=PRIMARY_BG)
        self.status_var = tk.StringVar(self.root, value="请先输入参数，然后点击“重新计算”。")

        self._configure_style()

        self._build_menu()
        self._build_layout()
        self.reset_defaults()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Root.TFrame", background=PRIMARY_BG)
        style.configure("Header.TLabel", background=PRIMARY_BG, foreground=TITLE_BG, font=("Microsoft YaHei UI", 17, "bold"))
        style.configure("Muted.TLabel", background=PRIMARY_BG, foreground=TEXT_MUTED, font=("Microsoft YaHei UI", 9))
        style.configure("Status.TLabel", background=PRIMARY_BG, foreground=TITLE_BG, font=("Microsoft YaHei UI", 9, "bold"))
        style.configure(
            "Toolbar.TButton",
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(12, 7),
            background=ACCENT_BG,
            foreground=TITLE_FG,
            bordercolor="#1d4a73",
        )
        style.map(
            "Toolbar.TButton",
            background=[("active", ACCENT_ACTIVE_BG), ("pressed", TITLE_BG)],
            foreground=[("disabled", "#d6e0ea"), ("!disabled", TITLE_FG)],
        )
        style.configure("Result.Treeview", rowheight=30, font=("Consolas", 10), background=PANEL_BG, fieldbackground=PANEL_BG)
        style.configure(
            "Result.Treeview.Heading",
            font=("Microsoft YaHei UI", 10, "bold"),
            background="#d9e2ec",
            foreground="#243746",
            relief="flat",
        )
        style.map("Result.Treeview.Heading", background=[("active", "#c7d3df")])
        style.configure("Panel.Vertical.TScrollbar", background="#d9e2ec", troughcolor="#f5f7fa", arrowcolor=TITLE_BG)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="历史计算结果", command=self.open_history_window_dialog)
        file_menu.add_command(label="退出", command=self.root.quit)
        menu.add_cascade(label="文件", menu=file_menu)

        calc_menu = tk.Menu(menu, tearoff=0)
        calc_menu.add_command(label="计算", command=self.calculate)
        calc_menu.add_command(label="恢复默认", command=self.reset_defaults)
        menu.add_cascade(label="计算", menu=calc_menu)

        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=10, style="Root.TFrame")
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        header = ttk.Frame(main, style="Root.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="汽车吊支腿反力计算", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="输入参数、查看结果、复核计算步骤并导出 Word 计算书",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        toolbar = ttk.Frame(main, style="Root.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        toolbar.columnconfigure(4, weight=1)

        ttk.Button(toolbar, text="重新计算", command=self.calculate, style="Toolbar.TButton").grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(toolbar, text="导出 Word 计算书", command=self.export_word, style="Toolbar.TButton").grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(toolbar, text="恢复默认", command=self.reset_defaults, style="Toolbar.TButton").grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(toolbar, text="清空输入", command=self.clear_inputs, style="Toolbar.TButton").grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Label(toolbar, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=4, sticky="e"
        )

        panes = ttk.Panedwindow(main, orient=tk.HORIZONTAL)
        panes.grid(row=2, column=0, sticky="nsew")

        input_panel = self._create_panel(panes, "输入参数")
        result_panel = self._create_panel(panes, "计算结果")
        steps_panel = self._create_panel(panes, "计算步骤（公式 / 代入 / 结果）")
        panes.add(input_panel, weight=3)
        panes.add(result_panel, weight=4)
        panes.add(steps_panel, weight=5)

        self._build_input_panel(input_panel.body)
        self._build_result_panel(result_panel.body)
        self._build_steps_panel(steps_panel.body)

    def _create_panel(self, parent: ttk.Panedwindow, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BORDER_COLOR, bd=0, highlightthickness=0)
        title_bar = tk.Frame(outer, bg=TITLE_BG, height=40)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(
            title_bar,
            text=title,
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=("Microsoft YaHei UI", 11, "bold"),
            anchor="w",
            padx=12,
        ).pack(fill=tk.BOTH, expand=True)
        body = tk.Frame(outer, bg=PANEL_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=1, pady=(0, 1))
        outer.body = body  # type: ignore[attr-defined]
        return outer

    def _build_input_panel(self, parent: tk.Frame) -> None:
        canvas = tk.Canvas(parent, highlightthickness=0, bg=PANEL_BG)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview, style="Panel.Vertical.TScrollbar")
        content = ttk.Frame(canvas, padding=10)

        content.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window, width=event.width),
        )

        field_map = {key: (label, unit) for key, label, unit in ALL_INPUT_FIELDS}
        row = 0
        for title, keys in INPUT_GROUPS:
            section = ttk.LabelFrame(content, text=title, padding=10)
            section.grid(row=row, column=0, sticky="ew", pady=(0, 10))
            section.columnconfigure(1, weight=1)
            for idx, key in enumerate(keys):
                label, unit = field_map[key]
                ttk.Label(section, text=label).grid(row=idx, column=0, sticky="w", pady=5, padx=(0, 8))
                entry = ttk.Entry(section, font=("Consolas", 10))
                entry.grid(row=idx, column=1, sticky="ew", pady=5)
                ttk.Label(section, text=unit, width=8, foreground=TEXT_MUTED).grid(
                    row=idx, column=2, sticky="w", padx=(8, 0)
                )
                self.entries[key] = entry
            row += 1

    def _build_result_panel(self, parent: tk.Frame) -> None:
        columns = ("name", "value", "unit")
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="Result.Treeview")
        tree.heading("name", text="项目")
        tree.heading("value", text="数值")
        tree.heading("unit", text="单位")
        tree.column("name", width=220, anchor="w")
        tree.column("value", width=120, anchor="e")
        tree.column("unit", width=80, anchor="center")

        tree.tag_configure("odd", background="#ffffff")
        tree.tag_configure("even", background="#f4f8fb")

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview, style="Panel.Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))

        self.result_tree = tree

    def _build_steps_panel(self, parent: tk.Frame) -> None:
        note = tk.Label(
            parent,
            text="按“公式 / 参数代入 / 结果”显示，便于校核与生成计算书",
            bg=PANEL_BG,
            fg=TEXT_MUTED,
            font=("Microsoft YaHei UI", 9),
            anchor="w",
            padx=10,
            pady=10,
        )
        note.pack(fill=tk.X)

        diagram_frame = tk.Frame(parent, bg=PANEL_BG)
        diagram_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Label(
            diagram_frame,
            text="计算简图",
            bg=PANEL_BG,
            fg=TITLE_BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            anchor="w",
            pady=4,
        ).pack(fill=tk.X)
        diagram_label = tk.Label(
            diagram_frame,
            text="正在加载计算简图...",
            bg="#fbfcfe",
            fg=TEXT_MUTED,
            relief="solid",
            bd=1,
            anchor="center",
            padx=8,
            pady=8,
        )
        diagram_label.configure(cursor="hand2")
        diagram_label.bind("<Button-1>", self._open_diagram_viewer)
        diagram_label.pack(fill=tk.X)
        tk.Label(
            diagram_frame,
            text="单击简图可放大查看",
            bg=PANEL_BG,
            fg=TEXT_MUTED,
            font=("Microsoft YaHei UI", 9),
            anchor="w",
            pady=2,
        ).pack(fill=tk.X)
        diagram_frame.bind("<Configure>", self._on_diagram_container_resize)
        self.diagram_container = diagram_frame
        self.diagram_label = diagram_label
        self._refresh_diagram()
        parent.after(100, self._refresh_diagram)

        text = tk.Text(
            parent,
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            bg="#fbfcfe",
            fg="#1f2933",
            insertbackground=TITLE_BG,
            relief="flat",
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text.yview, style="Panel.Vertical.TScrollbar")
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 10))
        self.steps_text = text

    def _refresh_diagram(self) -> None:
        if not self.diagram_label:
            return

        image_path = self._ensure_diagram_png()
        if not image_path or not image_path.exists():
            self.diagram_label.configure(text="未找到 Excel 中的计算简图。", image="", height=6)
            self.diagram_photo = None
            return

        try:
            photo = tk.PhotoImage(file=str(image_path))
        except tk.TclError:
            self.diagram_label.configure(text="计算简图加载失败。", image="", height=6)
            self.diagram_photo = None
            return

        width = photo.width()
        height = photo.height()
        container_width = 430
        if self.diagram_container and self.diagram_container.winfo_width() > 40:
            container_width = max(280, self.diagram_container.winfo_width() - 20)
        max_width = container_width
        max_height = 260
        scale_x = max(1, (width + max_width - 1) // max_width)
        scale_y = max(1, (height + max_height - 1) // max_height)
        scale = max(scale_x, scale_y)
        if scale > 1:
            photo = photo.subsample(scale, scale)

        self.diagram_photo = photo
        self.diagram_label.configure(image=self.diagram_photo, text="", height=photo.height())

    def _on_diagram_container_resize(self, _event: object) -> None:
        if self.diagram_label:
            self.diagram_label.after_idle(self._refresh_diagram)

    def _open_diagram_viewer(self, _event: object | None = None) -> None:
        image_path = self._ensure_diagram_png()
        if not image_path or not image_path.exists():
            messagebox.showinfo("提示", "未找到 Excel 中的计算简图。")
            return

        if self.diagram_viewer and self.diagram_viewer.winfo_exists():
            self.diagram_viewer.deiconify()
            self.diagram_viewer.lift()
            self.diagram_viewer_scale = (1, 1)
            self._load_diagram_viewer_image(fit=False)
            return

        window = tk.Toplevel(self.root)
        window.title("计算简图（放大查看）")
        window.geometry("980x720")
        window.configure(bg=PRIMARY_BG)
        window.transient(self.root)
        self.diagram_viewer = window

        header = tk.Frame(window, bg=TITLE_BG)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="计算简图（放大查看）",
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=("Microsoft YaHei UI", 12, "bold"),
            anchor="w",
            padx=12,
            pady=10,
        ).pack(side=tk.LEFT)

        toolbar = tk.Frame(window, bg=PRIMARY_BG)
        toolbar.pack(fill=tk.X, padx=12, pady=10)
        ttk.Button(toolbar, text="缩小", command=lambda: self._set_diagram_viewer_scale("out")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="放大", command=lambda: self._set_diagram_viewer_scale("in")).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="100%", command=lambda: self._set_diagram_viewer_scale((1, 1))).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="适应窗口", command=lambda: self._load_diagram_viewer_image(fit=True)).pack(side=tk.LEFT, padx=(8, 0))

        body = tk.Frame(window, bg=PANEL_BG, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        canvas = tk.Canvas(body, bg="#ffffff", highlightthickness=0)
        vsb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview, style="Panel.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(body, orient=tk.HORIZONTAL, command=canvas.xview, style="Panel.Horizontal.TScrollbar")
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.diagram_viewer_canvas = canvas
        self.diagram_viewer_scale = (1, 1)
        self._load_diagram_viewer_image(fit=False)

    def _set_diagram_viewer_scale(self, action: str | tuple[int, int]) -> None:
        scales = [(1, 4), (1, 2), (3, 4), (1, 1), (3, 2), (2, 1), (3, 1)]
        if isinstance(action, tuple):
            self.diagram_viewer_scale = action
            self._load_diagram_viewer_image()
            return

        try:
            idx = scales.index(self.diagram_viewer_scale)
        except ValueError:
            idx = 3

        if action == "in":
            idx = min(len(scales) - 1, idx + 1)
        else:
            idx = max(0, idx - 1)
        self.diagram_viewer_scale = scales[idx]
        self._load_diagram_viewer_image()

    def _load_diagram_viewer_image(self, fit: bool = False) -> None:
        if not self.diagram_viewer_canvas:
            return

        image_path = self._ensure_diagram_png()
        if not image_path or not image_path.exists():
            return

        try:
            base = tk.PhotoImage(file=str(image_path))
        except tk.TclError:
            return

        self.diagram_viewer_base = base

        if fit:
            canvas_w = max(1, self.diagram_viewer_canvas.winfo_width())
            canvas_h = max(1, self.diagram_viewer_canvas.winfo_height())
            target_w = max(1, canvas_w - 30)
            target_h = max(1, canvas_h - 30)
            scale_w = base.width() / target_w
            scale_h = base.height() / target_h
            scale = max(scale_w, scale_h, 1.0)
            den = int(scale) if scale >= 1 else 1
            self.diagram_viewer_scale = (1, max(1, den))

        num, den = self.diagram_viewer_scale
        photo = base
        if num > 1:
            photo = photo.zoom(num, num)
        if den > 1:
            photo = photo.subsample(den, den)

        self.diagram_viewer_photo = photo
        if self.diagram_viewer_image_id is None:
            self.diagram_viewer_image_id = self.diagram_viewer_canvas.create_image(0, 0, anchor="nw", image=self.diagram_viewer_photo)
        else:
            self.diagram_viewer_canvas.itemconfigure(self.diagram_viewer_image_id, image=self.diagram_viewer_photo)
        self.diagram_viewer_canvas.configure(scrollregion=(0, 0, photo.width(), photo.height()))

    def _ensure_diagram_png(self) -> Path | None:
        data_dir = _project_root() / "data"
        user_diagram_candidates = [
            data_dir / "计算简图.png",
            data_dir / "计算简图.PNG",
            data_dir / "diagram.png",
            data_dir / "DIAGRAM.PNG",
        ]
        for candidate in user_diagram_candidates:
            if candidate.exists():
                return candidate

        workbook = data_dir / "支腿反力验算.XLSX"
        emf_path = data_dir / "_diagram_cache_8x.emf"
        png_path = data_dir / "_diagram_cache_8x.png"
        old_files = [
            data_dir / "_diagram_cache.emf",
            data_dir / "_diagram_cache.png",
            data_dir / "_diagram_cache_3x.emf",
            data_dir / "_diagram_cache_3x.png",
        ]

        if not workbook.exists():
            return None

        needs_refresh = True
        if png_path.exists() and png_path.stat().st_mtime >= workbook.stat().st_mtime:
            needs_refresh = False

        if not needs_refresh:
            return png_path

        try:
            with ZipFile(workbook) as archive:
                media_files = [name for name in archive.namelist() if name.startswith("xl/media/")]
                emf_files = [name for name in media_files if name.lower().endswith(".emf")]
                target_name = emf_files[0] if emf_files else ""
                if not target_name:
                    return None
                emf_path.write_bytes(archive.read(target_name))
        except Exception:
            return None

        command = (
            "Add-Type -AssemblyName System.Drawing; "
            f"$src='{emf_path}'; "
            f"$dst='{png_path}'; "
            "$img=[System.Drawing.Image]::FromFile($src); "
            "$scale=8; "
            "$w=[int]($img.Width*$scale); "
            "$h=[int]($img.Height*$scale); "
            "$bmp=New-Object System.Drawing.Bitmap $w,$h; "
            "$g=[System.Drawing.Graphics]::FromImage($bmp); "
            "$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::HighQuality; "
            "$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic; "
            "$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality; "
            "$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality; "
            "$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit; "
            "$g.Clear([System.Drawing.Color]::White); "
            "$g.DrawImage($img,0,0,$w,$h); "
            "$bmp.Save($dst,[System.Drawing.Imaging.ImageFormat]::Png); "
            "$g.Dispose(); $bmp.Dispose(); $img.Dispose();"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=True,
                cwd=str(_project_root()),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return None

        try:
            for path in old_files:
                if path.exists():
                    path.unlink()
        except Exception:
            pass

        return png_path if png_path.exists() else None

    def _read_inputs(self) -> tuple[str, dict[str, float]]:
        model = self.entries["crane_model"].get().strip()
        if model == "":
            raise ValueError("请输入汽车吊型号")

        data: dict[str, float] = {}
        for k, _, _ in INPUT_FIELDS:
            v = self.entries[k].get().strip()
            if v == "":
                raise ValueError(f"请输入 {k}")
            data[k] = float(v)
        return model, data

    def calculate(self) -> None:
        try:
            model, data = self._read_inputs()
            report = calculate_report(data)
            report["inputs"] = {"crane_model": model, **report["inputs"]}  # type: ignore[index]
            self.last_report = report
            self._add_history(report)
            self._refresh_results(report["results"])  # type: ignore[arg-type]
            self._refresh_steps(report["steps"])  # type: ignore[arg-type]
            self.status_var.set(
                f"计算完成：{report['summary']}    时间：{datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self.status_var.set("计算失败，请检查输入参数。")
            messagebox.showerror("错误", str(e))

    def clear_inputs(self) -> None:
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.last_report = None
        self.status_var.set("已清空输入。")
        if self.result_tree:
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
        if self.steps_text:
            self.steps_text.delete("1.0", tk.END)

    def reset_defaults(self) -> None:
        self.clear_inputs()
        for key, value in DEFAULT_INPUTS.items():
            entry = self.entries.get(key)
            if entry:
                entry.insert(0, value)
        self.status_var.set("已恢复默认值，可直接录入参数。")

    def _add_history(self, report: dict[str, object]) -> None:
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report": deepcopy(report),
        }
        self.history.append(record)
        if len(self.history) > 100:
            self.history.pop(0)
        self._refresh_history_list()

    def open_history_window_dialog(self) -> None:
        if not self.history:
            messagebox.showinfo("提示", "当前还没有历史计算结果，请先完成一次计算。")
            return

        if self.history_window and self.history_window.winfo_exists():
            self.history_window.deiconify()
            self.history_window.lift()
            self._refresh_history_list()
            return

        window = tk.Toplevel(self.root)
        window.title("历史计算结果")
        window.geometry("760x420")
        window.configure(bg=PRIMARY_BG)
        window.transient(self.root)

        title = tk.Label(
            window,
            text="历史计算结果",
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=("Microsoft YaHei UI", 12, "bold"),
            anchor="w",
            padx=12,
            pady=10,
        )
        title.pack(fill=tk.X)

        body = tk.Frame(window, bg=PANEL_BG, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        note = tk.Label(
            body,
            text="点击某条历史记录后，主界面会自动显示对应的输入参数、计算结果和计算步骤。",
            bg=PANEL_BG,
            fg=TEXT_MUTED,
            font=("Microsoft YaHei UI", 9),
            anchor="w",
            padx=10,
            pady=10,
        )
        note.pack(fill=tk.X)

        list_frame = tk.Frame(body, bg=PANEL_BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        history_listbox = tk.Listbox(list_frame, font=("Consolas", 10), activestyle="none")
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=history_listbox.yview, style="Panel.Vertical.TScrollbar")
        history_listbox.configure(yscrollcommand=scrollbar.set)
        history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        action_bar = tk.Frame(body, bg=PANEL_BG)
        action_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(action_bar, text="加载选中记录", command=self._load_selected_history, style="Toolbar.TButton").pack(
            side=tk.LEFT
        )
        ttk.Button(action_bar, text="关闭", command=window.destroy, style="Toolbar.TButton").pack(side=tk.RIGHT)

        history_listbox.bind("<Double-Button-1>", self._on_history_activate)
        history_listbox.bind("<<ListboxSelect>>", self._on_history_select)

        self.history_window = window
        self.history_listbox = history_listbox
        window.protocol("WM_DELETE_WINDOW", self._close_history_window)
        self._refresh_history_list(select_last=True)

    def _close_history_window(self) -> None:
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.destroy()
        self.history_window = None
        self.history_listbox = None

    def _refresh_history_list(self, *, select_last: bool = False) -> None:
        if not self.history_listbox or not self.history_listbox.winfo_exists():
            return
        self.history_listbox.delete(0, tk.END)
        for index, item in enumerate(self.history, start=1):
            report = item["report"]
            summary = ""
            if isinstance(report, dict):
                summary = self._format_history_item(report)
            self.history_listbox.insert(tk.END, f"{index:02d}. {item['time']} | {summary}")
        if select_last and self.history:
            last = len(self.history) - 1
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(last)
            self.history_listbox.see(last)

    def _on_history_select(self, _event: object) -> None:
        self._load_selected_history()

    def _on_history_activate(self, _event: object) -> None:
        self._load_selected_history()

    def _load_selected_history(self) -> None:
        if not self.history_listbox or not self.history_listbox.winfo_exists():
            return
        selection = self.history_listbox.curselection()
        if not selection:
            return
        index = int(selection[0])
        if index < 0 or index >= len(self.history):
            return
        report = self.history[index]["report"]
        if not isinstance(report, dict):
            return
        self._load_report(report)

    def _load_report(self, report: dict[str, object]) -> None:
        self.last_report = deepcopy(report)
        inputs = report.get("inputs")
        results = report.get("results")
        steps = report.get("steps")

        if isinstance(inputs, dict):
            for key, value in inputs.items():
                entry = self.entries.get(str(key))
                if not entry:
                    continue
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

        if isinstance(results, dict):
            self._refresh_results(results)  # type: ignore[arg-type]
        if isinstance(steps, list):
            self._refresh_steps(steps)  # type: ignore[arg-type]

        summary = str(report.get("summary", ""))
        self.status_var.set(f"已加载历史计算结果：{summary}")

    def _format_history_item(self, report: dict[str, object]) -> str:
        inputs = report.get("inputs")
        results = report.get("results")
        if not isinstance(inputs, dict) or not isinstance(results, dict):
            return str(report.get("summary", ""))

        model = str(inputs.get("crane_model", ""))
        g1 = inputs.get("G1", "")
        n_max = results.get("N_max", "")
        pressure = results.get("P", "")

        try:
            g1_text = f"{float(g1):.3f} t"
        except (TypeError, ValueError):
            g1_text = str(g1)
        try:
            n_max_text = f"{float(n_max):.3f} kN"
        except (TypeError, ValueError):
            n_max_text = str(n_max)
        try:
            pressure_text = f"{float(pressure):.3f} kPa"
        except (TypeError, ValueError):
            pressure_text = str(pressure)

        model_text = f"{model} t" if model else ""
        return (
            f"型号：{model_text} | 起吊构件重量：{g1_text} | "
            f"最大支腿反力：{n_max_text} | 最大地面压强：{pressure_text}"
        )

    def _refresh_results(self, results: dict[str, float]) -> None:
        if not self.result_tree:
            return
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        for index, (key, label, unit) in enumerate(OUTPUT_FIELDS):
            tag = "even" if index % 2 == 0 else "odd"
            self.result_tree.insert("", tk.END, values=(label, f"{results[key]:.3f}", unit), tags=(tag,))

    def _refresh_steps(self, steps: list[dict[str, str]]) -> None:
        if not self.steps_text:
            return
        self.steps_text.delete("1.0", tk.END)
        for step in steps:
            self.steps_text.insert(tk.END, f"{step['index']}. {step['title']}\n")
            self.steps_text.insert(tk.END, f"计算公式：{step['formula']}\n")
            self.steps_text.insert(tk.END, f"参数代入：{step['substitution']}\n")
            self.steps_text.insert(tk.END, f"计算结果：{step['result']}\n\n")

    def export_word(self) -> None:
        if not self.last_report:
            messagebox.showwarning("提示", "请先完成一次计算，再导出 Word 计算书。")
            return

        file = filedialog.asksaveasfilename(
            title="导出 Word 计算书",
            defaultextension=".docx",
            filetypes=[("Word 文档", "*.docx")],
            initialfile="支腿反力计算书.docx",
        )
        if not file:
            return

        try:
            self._write_docx(Path(file), self.last_report)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return

        self.status_var.set(f"Word 计算书已导出：{file}")
        messagebox.showinfo("成功", "Word 计算书导出完成。")

    def _write_docx(self, file_path: Path, report: dict[str, object]) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image_path = self._ensure_diagram_png()
        has_image = bool(image_path and image_path.exists())
        document_xml = self._build_document_xml(report, now, has_image=has_image)
        styles_xml = self._build_styles_xml()
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
        core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>汽车吊支腿反力计算书</dc:title>
  <dc:creator>TRAE</dc:creator>
  <cp:lastModifiedBy>TRAE</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{datetime.now().isoformat()}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{datetime.now().isoformat()}</dcterms:modified>
</cp:coreProperties>
"""
        app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
</Properties>
"""
        doc_rels_body = []
        doc_rels_body.append(
            '  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        )
        if has_image:
            doc_rels_body.append(
                '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/diagram.png"/>'
            )
        doc_rels = (
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
"""
            + "\n".join(doc_rels_body)
            + ("\n" if doc_rels_body else "")
            + "</Relationships>\n"
        )

        with ZipFile(file_path, "w", compression=ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", content_types)
            docx.writestr("_rels/.rels", rels)
            docx.writestr("docProps/core.xml", core)
            docx.writestr("docProps/app.xml", app)
            docx.writestr("word/document.xml", document_xml)
            docx.writestr("word/styles.xml", styles_xml)
            docx.writestr("word/_rels/document.xml.rels", doc_rels)
            if has_image and image_path:
                docx.writestr("word/media/diagram.png", image_path.read_bytes())

    def _build_document_xml(self, report: dict[str, object], now: str, *, has_image: bool) -> str:
        inputs = report["inputs"]  # type: ignore[assignment]
        results = report["results"]  # type: ignore[assignment]

        body: list[str] = []
        body.append(
            self._docx_paragraph(
                "汽车吊相关验算计算书",
                bold=True,
                size=40,
                center=True,
                color="1F4D78",
                style="Title",
                indent=False,
            )
        )
        body.append(self._docx_paragraph(f"生成时间：{now}", size=21, center=True, indent=False))
        body.append(self._docx_paragraph(""))

        crane_model = str(inputs.get("crane_model", ""))  # type: ignore[union-attr]
        model_text = f"{crane_model}吨汽车吊" if crane_model else "汽车吊"
        body.append(self._docx_paragraph("1 汽车吊支腿反力计算", bold=True, size=28, style="Heading1", indent=False))
        body.append(self._docx_paragraph("1.1 计算目的", bold=True, size=24, style="Heading2", indent=False))
        body.append(
            self._docx_paragraph(
                f"为校核{model_text}吊装作业时各支腿反力及地面最大压强，判断路基箱及地基承载条件是否满足吊装要求。"
            )
        )

        body.append(self._docx_paragraph("1.2 计算参数", bold=True, size=24, style="Heading2", indent=False))
        param_rows = [["参数", "符号", "数值", "单位"]]
        if crane_model:
            param_rows.append(["汽车吊型号", "Model", crane_model, "t"])
        for key, label, unit in INPUT_FIELDS:
            value = inputs[key]  # type: ignore[index]
            param_rows.append([label, key, f"{value:.3f}", unit])
        body.append(self._docx_table(param_rows, [4536, 1224, 1656, 1584], header_rows=1))

        body.append(self._docx_paragraph(""))
        body.append(self._docx_paragraph("1.3 计算公式及简图", bold=True, size=24, style="Heading2", indent=False))
        formula_lines = [
            "总竖向力 F = (G0 + G1 + G2 + G3) × g",
            "总弯矩 M = (G1 × L1 - G2 × C + G3 × E) × g",
            "水平夹角 β = arctan(B / 2D)",
            "X 轴弯矩 Mx = M × cosβ",
            "Y 轴弯矩 My = M × sinβ",
            "支腿 1 反力 N1 = D × F / 2A - Mx / 2A + My / 2B",
            "支腿 2 反力 N2 = (A - D) × F / 2A + Mx / 2A + My / 2B",
            "支腿 3 反力 N3 = D × F / 2A - Mx / 2A - My / 2B",
            "支腿 4 反力 N4 = (A - D) × F / 2A + Mx / 2A - My / 2B",
            "最大地面压强 P = Nmax / S",
        ]
        for line in formula_lines:
            body.append(self._docx_paragraph(line))
        if has_image:
            body.append(self._docx_paragraph("计算简图", bold=True, size=22, indent=False))
            body.append(self._docx_image_paragraph("rId1"))
            body.append(self._docx_paragraph("支腿反力验算计算简图", center=True, size=19, indent=False))

        body.append(self._docx_paragraph("1.4 计算结果", bold=True, size=24, style="Heading2", indent=False))
        result_rows = [["项目", "符号", "数值", "单位"]]
        for key, label, unit in OUTPUT_FIELDS:
            value = results[key]  # type: ignore[index]
            result_rows.append([label, key, f"{value:.3f}", unit])
        body.append(self._docx_table(result_rows, [4536, 1224, 1656, 1584], header_rows=1))

        body.append(self._docx_paragraph(""))
        body.append(self._docx_paragraph("1.5 结论", bold=True, size=24, style="Heading2", indent=False))
        n_max = float(results["N_max"])  # type: ignore[index]
        pressure = float(results["P"])  # type: ignore[index]
        body.append(
            self._docx_paragraph(
                f"经计算，本工况下汽车吊最大支腿反力为 {n_max:.3f} kN，对应最大地面压强为 {pressure:.3f} kPa。"
                "后续应将该压强与现场地基承载力或铺设路基箱后的允许承载力进行比较；"
                "若允许承载力大于该值，则支腿承载满足要求。"
            )
        )

        return (
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
<w:body>"""
            + "".join(body)
            + """<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>"""
        )

    def _docx_paragraph(
        self,
        text: str,
        *,
        bold: bool = False,
        size: int = 24,
        center: bool = False,
        color: str | None = None,
        style: str | None = None,
        indent: bool | None = None,
    ) -> str:
        escaped = escape(text)
        align = '<w:jc w:val="center"/>' if center else ""
        weight = "<w:b/>" if bold else ""
        color_xml = f'<w:color w:val="{color}"/>' if color else ""
        style_xml = f'<w:pStyle w:val="{style}"/>' if style else ""
        use_indent = indent if indent is not None else (not center)
        if text.strip():
            indent_xml = '<w:ind w:firstLine="420"/>' if use_indent else '<w:ind w:firstLine="0"/>'
        else:
            indent_xml = ""
        return (
            "<w:p><w:pPr><w:spacing w:before=\"60\" w:after=\"60\" w:line=\"360\" w:lineRule=\"auto\"/>"
            f"{style_xml}{align}{indent_xml}"
            "</w:pPr><w:r><w:rPr>"
            f"{weight}{color_xml}<w:rFonts w:ascii=\"Calibri\" w:hAnsi=\"Calibri\" w:eastAsia=\"宋体\"/>"
            f"<w:sz w:val=\"{size}\"/><w:szCs w:val=\"{size}\"/>"
            "</w:rPr><w:t xml:space=\"preserve\">"
            f"{escaped}"
            "</w:t></w:r></w:p>"
        )

    def _build_styles_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
        <w:sz w:val="24"/>
        <w:szCs w:val="24"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:before="60" w:after="60" w:line="360" w:lineRule="auto"/>
        <w:ind w:firstLine="420"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="60" w:after="60" w:line="360" w:lineRule="auto"/>
      <w:ind w:firstLine="420"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
      <w:sz w:val="24"/>
      <w:szCs w:val="24"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:uiPriority w:val="10"/>
    <w:qFormat/>
    <w:pPr>
      <w:jc w:val="center"/>
      <w:spacing w:before="120" w:after="160"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:color w:val="1F4D78"/>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
      <w:sz w:val="40"/>
      <w:szCs w:val="40"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:uiPriority w:val="9"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="140" w:after="100"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
      <w:sz w:val="28"/>
      <w:szCs w:val="28"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:uiPriority w:val="9"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="120" w:after="80"/>
      <w:outlineLvl w:val="1"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
      <w:sz w:val="24"/>
      <w:szCs w:val="24"/>
    </w:rPr>
  </w:style>
</w:styles>
"""

    def _docx_table(self, rows: list[list[str]], widths: list[int], *, header_rows: int = 0) -> str:
        grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
        row_xml: list[str] = []
        for row_index, row in enumerate(rows):
            cells: list[str] = []
            for col_index, value in enumerate(row):
                width = widths[min(col_index, len(widths) - 1)]
                is_header = row_index < header_rows
                shading = '<w:shd w:val="clear" w:color="auto" w:fill="F2F4F7"/>' if is_header else ""
                paragraph = self._docx_paragraph(value, bold=is_header, center=True, size=24, indent=False)
                cells.append(
                    "<w:tc><w:tcPr>"
                    f'<w:tcW w:w="{width}" w:type="dxa"/>'
                    f"{shading}<w:vAlign w:val=\"center\"/></w:tcPr>"
                    f"{paragraph}</w:tc>"
                )
            row_xml.append(f"<w:tr>{''.join(cells)}</w:tr>")

        return (
            "<w:tbl><w:tblPr>"
            '<w:tblW w:w="0" w:type="auto"/>'
            '<w:jc w:val="center"/>'
            "<w:tblBorders>"
            '<w:top w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
            '<w:left w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
            '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
            '<w:right w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
            '<w:insideH w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
            '<w:insideV w:val="single" w:sz="6" w:space="0" w:color="B8C2CC"/>'
            "</w:tblBorders>"
            '<w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tblCellMar>'
            "</w:tblPr>"
            f"<w:tblGrid>{grid}</w:tblGrid>"
            + "".join(row_xml)
            + "</w:tbl>"
        )

    def _docx_image_paragraph(self, rel_id: str) -> str:
        image_path = self._ensure_diagram_png()
        width_px, height_px = self._get_png_size(image_path) if image_path else (800, 600)
        max_width_emu = 5_600_000
        width_emu = width_px * 9525
        height_emu = height_px * 9525
        if width_emu > max_width_emu:
            height_emu = int(height_emu * max_width_emu / width_emu)
            width_emu = max_width_emu
        return (
            '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            '<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
            '<wp:docPr id="1" name="计算简图"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic>'
            '<pic:nvPicPr><pic:cNvPr id="0" name="diagram.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
        )

    def _get_png_size(self, file_path: Path) -> tuple[int, int]:
        try:
            with file_path.open("rb") as handle:
                header = handle.read(24)
            if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
                width, height = struct.unpack(">II", header[16:24])
                return max(1, width), max(1, height)
        except Exception:
            pass
        return (800, 600)


def run() -> None:
    app = App()
    app.root.mainloop()


if __name__ == "__main__":
    run()

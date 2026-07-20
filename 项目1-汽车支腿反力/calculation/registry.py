from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .anti_overturning import calculate_report as calculate_anti_overturning_report
from .crane import calculate_report as calculate_support_reaction_report


ReportBuilder = Callable[[dict[str, float]], dict[str, object]]


@dataclass(frozen=True)
class FieldDef:
    key: str
    label: str
    unit: str


@dataclass(frozen=True)
class GroupDef:
    title: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class CalculatorConfig:
    key: str
    title: str
    subtitle: str
    doc_title: str
    input_fields: tuple[FieldDef, ...]
    input_groups: tuple[GroupDef, ...]
    output_fields: tuple[FieldDef, ...]
    default_inputs: dict[str, str]
    calculate_report: ReportBuilder
    diagram_candidates: tuple[str, ...]
    workbook_name: str | None = None


MODEL_FIELD = FieldDef("crane_model", "汽车吊型号", "t")


SUPPORT_REACTION_FIELDS = (
    FieldDef("G3", "汽车吊吊臂自重 G3", "t"),
    FieldDef("E", "吊臂重心至回转中心 E", "m"),
    FieldDef("G0", "汽车吊自重（扣除吊臂重量） G0", "t"),
    FieldDef("G1", "起吊构件最大重量 G1", "t"),
    FieldDef("G2", "配重 G2", "t"),
    FieldDef("L1", "起吊作业半径 L1", "m"),
    FieldDef("A", "支腿纵距 A", "m"),
    FieldDef("B", "支腿横距 B", "m"),
    FieldDef("C", "配重至回转中心距离 C", "m"),
    FieldDef("g", "重力加速度 g", "m/s²"),
    FieldDef("D", "回转中心至后支腿距离 D", "m"),
    FieldDef("a", "路基箱长 a", "m"),
    FieldDef("b", "路基箱宽 b", "m"),
)

SUPPORT_REACTION_GROUPS = (
    GroupDef("基本信息", ("crane_model",)),
    GroupDef("荷载参数", ("G0", "G1", "G2", "G3", "g")),
    GroupDef("布置参数", ("E", "L1", "A", "B", "C", "D")),
    GroupDef("基础参数", ("a", "b")),
)

SUPPORT_REACTION_OUTPUTS = (
    FieldDef("β", "水平角 β", "°"),
    FieldDef("cosβ", "cosβ", "-"),
    FieldDef("sinβ", "sinβ", "-"),
    FieldDef("F", "总竖向力 F", "kN"),
    FieldDef("M", "总弯矩 M", "kN·m"),
    FieldDef("Mx", "X 轴弯矩 Mx", "kN·m"),
    FieldDef("My", "Y 轴弯矩 My", "kN·m"),
    FieldDef("N1", "支腿 1 反力 N1", "kN"),
    FieldDef("N2", "支腿 2 反力 N2", "kN"),
    FieldDef("N3", "支腿 3 反力 N3", "kN"),
    FieldDef("N4", "支腿 4 反力 N4", "kN"),
    FieldDef("S", "路基箱面积 S", "m²"),
    FieldDef("P", "最大地面压强 P", "kPa"),
    FieldDef("N_max", "最大支腿反力 Nmax", "kN"),
)

SUPPORT_REACTION_DEFAULTS = {
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
    "a": "2",
    "b": "2",
}


ANTI_OVERTURNING_FIELDS = (
    FieldDef("G", "汽车吊自重 G", "t"),
    FieldDef("Q", "起吊构件最大重量 Q", "t"),
    FieldDef("G1", "配重 G1", "t"),
    FieldDef("R", "起吊作业半径 R", "m"),
    FieldDef("H", "风动载合力点高度 H", "m"),
    FieldDef("a", "汽车吊重心至支脚倾覆支点距离 a", "m"),
    FieldDef("C", "配重至回转中心距离 C", "m"),
    FieldDef("g", "重力加速度 g", "m/s²"),
    FieldDef("KG", "自重加权系数 KG", "-"),
    FieldDef("KQ", "起升荷载加权系数 KQ", "-"),
    FieldDef("KW", "风荷载加权系数 KW", "-"),
)

ANTI_OVERTURNING_GROUPS = (
    GroupDef("基本信息", ("crane_model",)),
    GroupDef("荷载参数", ("G", "Q", "G1", "g")),
    GroupDef("工况参数", ("R", "H", "a", "C")),
    GroupDef("系数参数", ("KG", "KQ", "KW")),
)

ANTI_OVERTURNING_OUTPUTS = (
    FieldDef("W", "风荷载 W", "kN"),
    FieldDef("MG", "汽车吊总重对倾覆边的力矩 MG", "kN·m"),
    FieldDef("MQ", "起升荷载对倾覆边的力矩 MQ", "kN·m"),
    FieldDef("MW", "风荷载对倾覆边的力矩 MW", "kN·m"),
    FieldDef("M", "倾覆边合力矩 M", "kN·m"),
    FieldDef("verdict", "结果判定", ""),
)

ANTI_OVERTURNING_DEFAULTS = {
    "crane_model": "300",
    "G": "72",
    "Q": "27",
    "G1": "100",
    "R": "20",
    "H": "22",
    "a": "4.3",
    "C": "5.75",
    "g": "9.8",
    "KG": "1",
    "KQ": "1.15",
    "KW": "1",
}


CALCULATORS: dict[str, CalculatorConfig] = {
    "support_reaction": CalculatorConfig(
        key="support_reaction",
        title="汽车吊支腿反力计算",
        subtitle="输入参数、查看结果、复核支腿反力与地面压强并导出计算书",
        doc_title="汽车吊支腿反力计算书",
        input_fields=SUPPORT_REACTION_FIELDS,
        input_groups=SUPPORT_REACTION_GROUPS,
        output_fields=SUPPORT_REACTION_OUTPUTS,
        default_inputs=SUPPORT_REACTION_DEFAULTS,
        calculate_report=calculate_support_reaction_report,
        diagram_candidates=("data/计算简图.png", "data/diagram.png"),
        workbook_name="支腿反力验算.XLSX",
    ),
    "anti_overturning": CalculatorConfig(
        key="anti_overturning",
        title="汽车吊抗倾覆验算",
        subtitle="输入工况参数、校核抗倾覆力矩并导出对应计算书",
        doc_title="汽车吊抗倾覆验算计算书",
        input_fields=ANTI_OVERTURNING_FIELDS,
        input_groups=ANTI_OVERTURNING_GROUPS,
        output_fields=ANTI_OVERTURNING_OUTPUTS,
        default_inputs=ANTI_OVERTURNING_DEFAULTS,
        calculate_report=calculate_anti_overturning_report,
        diagram_candidates=("data/汽车吊抗倾覆计算简图.png",),
        workbook_name="汽车吊抗倾覆验算.xlsx",
    ),
}

DEFAULT_CALCULATOR_KEY = "support_reaction"


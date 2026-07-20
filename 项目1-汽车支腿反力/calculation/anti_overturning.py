import math


Step = dict[str, str]


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _step(index: int, title: str, formula: str, substitution: str, result: str) -> Step:
    return {
        "index": str(index),
        "title": title,
        "formula": formula,
        "substitution": substitution,
        "result": result,
    }


def calculate_report(data: dict[str, float]) -> dict[str, object]:
    if data["g"] == 0:
        raise ValueError("重力加速度 g 不能为0")

    wind_load = data["Q"] * 0.2 * data["g"]
    mg = data["G"] * data["g"] * data["a"] + data["G1"] * data["g"] * (data["a"] + data["C"])
    mq = -data["Q"] * data["g"] * (data["R"] - data["a"])
    mw = -wind_load * data["H"]
    moment = data["KG"] * mg + data["KQ"] * mq + data["KW"] * mw
    verdict = "满足要求" if moment > 0 else "不满足要求"

    results = {
        "W": wind_load,
        "MG": mg,
        "MQ": mq,
        "MW": mw,
        "M": moment,
        "verdict": verdict,
    }

    steps = [
        _step(
            1,
            "风荷载 W",
            "W = 20% x Q x g",
            f"W = 20% x {_fmt(data['Q'])} x {_fmt(data['g'])}",
            f"W = {_fmt(wind_load)} kN",
        ),
        _step(
            2,
            "汽车吊总重对倾覆边的力矩 MG",
            "MG = G x g x a + G1 x g x (a + C)",
            (
                f"MG = {_fmt(data['G'])} x {_fmt(data['g'])} x {_fmt(data['a'])} + "
                f"{_fmt(data['G1'])} x {_fmt(data['g'])} x ({_fmt(data['a'])} + {_fmt(data['C'])})"
            ),
            f"MG = {_fmt(mg)} kN·m",
        ),
        _step(
            3,
            "起升荷载对倾覆边的力矩 MQ",
            "MQ = -Q x g x (R - a)",
            f"MQ = -{_fmt(data['Q'])} x {_fmt(data['g'])} x ({_fmt(data['R'])} - {_fmt(data['a'])})",
            f"MQ = {_fmt(mq)} kN·m",
        ),
        _step(
            4,
            "风荷载对倾覆边的力矩 MW",
            "MW = -W x H",
            f"MW = -{_fmt(wind_load)} x {_fmt(data['H'])}",
            f"MW = {_fmt(mw)} kN·m",
        ),
        _step(
            5,
            "倾覆边合力矩 M",
            "M = KG x MG + KQ x MQ + KW x MW",
            (
                f"M = {_fmt(data['KG'])} x {_fmt(mg)} + {_fmt(data['KQ'])} x {_fmt(mq)} + "
                f"{_fmt(data['KW'])} x {_fmt(mw)}"
            ),
            f"M = {_fmt(moment)} kN·m",
        ),
        _step(
            6,
            "结果判定",
            "M > 0",
            f"{_fmt(moment)} > 0",
            verdict,
        ),
    ]

    return {
        "inputs": data,
        "results": results,
        "steps": steps,
        "summary": f"倾覆边合力矩 M = {_fmt(moment)} kN·m，{verdict}",
        "conclusion": (
            f"经计算，本工况下汽车吊抗倾覆合力矩为 {_fmt(moment)} kN·m，判定结果为“{verdict}”。"
            if verdict == "满足要求"
            else f"经计算，本工况下汽车吊抗倾覆合力矩为 {_fmt(moment)} kN·m，判定结果为“{verdict}”，需调整工况参数。"
        ),
    }

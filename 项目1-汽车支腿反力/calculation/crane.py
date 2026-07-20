import math

from .foundation import ground_pressure


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
    if data["D"] == 0:
        raise ValueError("回转中心至后支腿距离 D 不能为0")
    if data["A"] == 0:
        raise ValueError("支腿纵距 A 不能为0")
    if data["B"] == 0:
        raise ValueError("支腿横距 B 不能为0")

    beta = math.degrees(math.atan(data["B"] / (2 * data["D"])))
    beta_rad = math.radians(beta)

    cos_beta = math.cos(beta_rad)
    sin_beta = math.sin(beta_rad)

    f = (data["G0"] + data["G1"] + data["G2"] + data["G3"]) * data["g"]
    m = (data["G1"] * data["L1"] - data["G2"] * data["C"] + data["G3"] * data["E"]) * data["g"]

    mx = m * cos_beta
    my = m * sin_beta

    n1 = data["D"] * f / (2 * data["A"]) - mx / (2 * data["A"]) + my / (2 * data["B"])
    n2 = (data["A"] - data["D"]) * f / (2 * data["A"]) + mx / (2 * data["A"]) + my / (2 * data["B"])
    n3 = data["D"] * f / (2 * data["A"]) - mx / (2 * data["A"]) - my / (2 * data["B"])
    n4 = (data["A"] - data["D"]) * f / (2 * data["A"]) + mx / (2 * data["A"]) - my / (2 * data["B"])

    n_max = max(n1, n2, n3, n4)
    s, p = ground_pressure(n_max, data["a"], data["b"])

    results = {
        "β": beta,
        "cosβ": cos_beta,
        "sinβ": sin_beta,
        "F": f,
        "M": m,
        "Mx": mx,
        "My": my,
        "N1": n1,
        "N2": n2,
        "N3": n3,
        "N4": n4,
        "S": s,
        "P": p,
        "N_max": n_max,
    }

    steps = [
        _step(
            1,
            "水平角 β",
            "β = arctan(B / (2D))",
            f"β = arctan({_fmt(data['B'])} / (2 x {_fmt(data['D'])}))",
            f"β = {_fmt(beta)} deg",
        ),
        _step(
            2,
            "三角函数值",
            "cosβ = cos(β), sinβ = sin(β)",
            f"cosβ = cos({_fmt(beta)} deg), sinβ = sin({_fmt(beta)} deg)",
            f"cosβ = {_fmt(cos_beta)}, sinβ = {_fmt(sin_beta)}",
        ),
        _step(
            3,
            "总竖向力 F",
            "F = (G0 + G1 + G2 + G3) x g",
            (
                f"F = ({_fmt(data['G0'])} + {_fmt(data['G1'])} + {_fmt(data['G2'])} + "
                f"{_fmt(data['G3'])}) x {_fmt(data['g'])}"
            ),
            f"F = {_fmt(f)} kN",
        ),
        _step(
            4,
            "总弯矩 M",
            "M = (G1 x L1 - G2 x C + G3 x E) x g",
            (
                f"M = ({_fmt(data['G1'])} x {_fmt(data['L1'])} - {_fmt(data['G2'])} x "
                f"{_fmt(data['C'])} + {_fmt(data['G3'])} x {_fmt(data['E'])}) x {_fmt(data['g'])}"
            ),
            f"M = {_fmt(m)} kN*m",
        ),
        _step(
            5,
            "X、Y 轴弯矩",
            "Mx = M x cosβ, My = M x sinβ",
            f"Mx = {_fmt(m)} x {_fmt(cos_beta)}, My = {_fmt(m)} x {_fmt(sin_beta)}",
            f"Mx = {_fmt(mx)} kN*m, My = {_fmt(my)} kN*m",
        ),
        _step(
            6,
            "支腿 1 反力 N1",
            "N1 = D x F / (2A) - Mx / (2A) + My / (2B)",
            (
                f"N1 = {_fmt(data['D'])} x {_fmt(f)} / (2 x {_fmt(data['A'])}) - {_fmt(mx)} / "
                f"(2 x {_fmt(data['A'])}) + {_fmt(my)} / (2 x {_fmt(data['B'])})"
            ),
            f"N1 = {_fmt(n1)} kN",
        ),
        _step(
            7,
            "支腿 2 反力 N2",
            "N2 = (A - D) x F / (2A) + Mx / (2A) + My / (2B)",
            (
                f"N2 = ({_fmt(data['A'])} - {_fmt(data['D'])}) x {_fmt(f)} / (2 x {_fmt(data['A'])}) + "
                f"{_fmt(mx)} / (2 x {_fmt(data['A'])}) + {_fmt(my)} / (2 x {_fmt(data['B'])})"
            ),
            f"N2 = {_fmt(n2)} kN",
        ),
        _step(
            8,
            "支腿 3 反力 N3",
            "N3 = D x F / (2A) - Mx / (2A) - My / (2B)",
            (
                f"N3 = {_fmt(data['D'])} x {_fmt(f)} / (2 x {_fmt(data['A'])}) - {_fmt(mx)} / "
                f"(2 x {_fmt(data['A'])}) - {_fmt(my)} / (2 x {_fmt(data['B'])})"
            ),
            f"N3 = {_fmt(n3)} kN",
        ),
        _step(
            9,
            "支腿 4 反力 N4",
            "N4 = (A - D) x F / (2A) + Mx / (2A) - My / (2B)",
            (
                f"N4 = ({_fmt(data['A'])} - {_fmt(data['D'])}) x {_fmt(f)} / (2 x {_fmt(data['A'])}) + "
                f"{_fmt(mx)} / (2 x {_fmt(data['A'])}) - {_fmt(my)} / (2 x {_fmt(data['B'])})"
            ),
            f"N4 = {_fmt(n4)} kN",
        ),
        _step(
            10,
            "最大支腿反力",
            "Nmax = max(N1, N2, N3, N4)",
            f"Nmax = max({_fmt(n1)}, {_fmt(n2)}, {_fmt(n3)}, {_fmt(n4)})",
            f"Nmax = {_fmt(n_max)} kN",
        ),
        _step(
            11,
            "路基箱面积",
            "S = a x b",
            f"S = {_fmt(data['a'])} x {_fmt(data['b'])}",
            f"S = {_fmt(s)} m^2",
        ),
        _step(
            12,
            "最大地面压强",
            "P = Nmax / S",
            f"P = {_fmt(n_max)} / {_fmt(s)}" if s else "S = 0，按 0 处理",
            f"P = {_fmt(p)} kPa",
        ),
    ]

    return {
        "inputs": data,
        "results": results,
        "steps": steps,
        "summary": f"最大支腿反力 Nmax = {_fmt(n_max)} kN，最大地面压强 P = {_fmt(p)} kPa",
        "conclusion": (
            f"经计算，本工况下汽车吊最大支腿反力为 {_fmt(n_max)} kN，对应最大地面压强为 {_fmt(p)} kPa。"
            "后续应将该压强与现场地基承载力或铺设路基箱后的允许承载力进行比较；"
            "若允许承载力大于该值，则支腿承载满足要求。"
        ),
    }


def calculate(data: dict[str, float]) -> dict[str, float]:
    report = calculate_report(data)
    return report["results"]  # type: ignore[return-value]

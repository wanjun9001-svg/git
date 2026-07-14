import math

from .foundation import ground_pressure


def calculate(data: dict[str, float]) -> dict[str, float]:
    if data["D"] == 0:
        raise ValueError("回转中心至后支腿距离 D 不能为0")

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

    return {
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


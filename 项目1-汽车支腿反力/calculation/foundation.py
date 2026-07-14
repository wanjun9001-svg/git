def ground_area(a: float, b: float) -> float:
    return a * b


def ground_pressure(n_max: float, a: float, b: float) -> tuple[float, float]:
    s = ground_area(a, b)
    p = n_max / s if s else 0.0
    return s, p


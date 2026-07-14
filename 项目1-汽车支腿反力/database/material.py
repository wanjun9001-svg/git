from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    name: str
    unit_weight_kn_m3: float


DEFAULT_MATERIALS: tuple[Material, ...] = (
    Material(name="钢", unit_weight_kn_m3=78.5),
    Material(name="混凝土", unit_weight_kn_m3=25.0),
)


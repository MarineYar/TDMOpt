"""MATPOWER-consistent branch coefficients on each network's declared base."""
from __future__ import annotations
import cmath
import math
import numpy as np


def branch_admittance(branch: dict) -> tuple[complex, complex, complex, complex]:
    """Return (Yff,Yft,Ytf,Ytt), preserving charging, tap and phase shift."""
    if not branch.get('status', 1):
        return 0j, 0j, 0j, 0j
    impedance = complex(branch['r_pu'], branch['x_pu'])
    if impedance == 0:
        raise ValueError('zero series branch impedance')
    series = 1 / impedance
    tap = branch.get('tap', 1.0) or 1.0
    a = tap * cmath.exp(1j * math.radians(branch.get('shift_degree', 0.0)))
    diagonal = series + .5j * branch.get('b_pu', 0.0)
    return diagonal / (a*a.conjugate()), -series/a.conjugate(), -series/a, diagonal


def ybus(network: dict) -> np.ndarray:
    """Return Ybus in the explicit input bus-row order, including bus shunts."""
    index = {b['id']: i for i, b in enumerate(network['buses'])}
    if len(index) != len(network['buses']):
        raise ValueError('duplicate bus IDs')
    result = np.zeros((len(index), len(index)), dtype=complex)
    for branch in network['branches']:
        i, j = index[branch['from_bus']], index[branch['to_bus']]
        ff, ft, tf, tt = branch_admittance(branch)
        result[i, i] += ff; result[i, j] += ft
        result[j, i] += tf; result[j, j] += tt
    for bus in network['buses']:
        result[index[bus['id']], index[bus['id']]] += complex(bus.get('gs_mw', 0), bus.get('bs_mvar', 0)) / network['base_mva']
    return result


def rebase_impedance(z_pu: complex | float, old_mva: float, new_mva: float,
                     old_kv: float, new_kv: float) -> complex | float:
    """Change bases for the same physical impedance (not capacity similarity)."""
    if min(old_mva, new_mva, old_kv, new_kv) <= 0:
        raise ValueError('electrical bases must be positive')
    return z_pu * (new_mva/old_mva) * (old_kv/new_kv)**2

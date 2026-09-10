import numpy as np


def rssi_to_distance(rssi, tx_power=-40, n=2.0):
    """Log-distance path loss model: d = 10^((tx_power - rssi) / (10*n))"""
    return 10 ** ((tx_power - rssi) / (10.0 * n))


def trilaterate_ls(node_positions, distances):
    """
    Weighted least-squares trilateration for 3+ anchor points.

    Linearises the system by subtracting one reference anchor equation
    from the others, producing Ax = b. Weights are the inverse-square
    distances so closer (more reliable) readings contribute more.

    Returns (x, y) rounded to 3 dp, or None if the system is degenerate.
    """
    n = len(node_positions)
    if n < 3:
        return None

    P = np.array(node_positions, dtype=float)
    d = np.array(distances, dtype=float)

    ref_p = P[-1]
    ref_d = d[-1]

    A = 2.0 * (P[:-1] - ref_p)
    b = (
        np.sum(P[:-1] ** 2, axis=1)
        - np.sum(ref_p ** 2)
        - d[:-1] ** 2
        + ref_d ** 2
    )

    w = 1.0 / np.maximum(d[:-1], 0.1) ** 2
    W = np.diag(w)

    result, _, rank, _ = np.linalg.lstsq(W @ A, W @ b, rcond=None)

    if rank < 2:
        return None

    return round(float(result[0]), 3), round(float(result[1]), 3)

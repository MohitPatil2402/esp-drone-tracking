import math

def rssi_to_distance(rssi, tx_power=-40, n=2):
    return 10 ** ((tx_power - rssi) / (10 * n))

def trilaterate(p1, p2, p3, r1, r2, r3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    A = 2 * (x2 - x1)
    B = 2 * (y2 - y1)
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2

    D = 2 * (x3 - x2)
    E = 2 * (y3 - y2)
    F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

    denom1 = (A * E - B * D)
    denom2 = (B * D - A * E)

    if denom1 == 0 or denom2 == 0:
        return None

    x = (C * E - F * B) / denom1
    y = (C * D - A * F) / denom2

    return (x, y)
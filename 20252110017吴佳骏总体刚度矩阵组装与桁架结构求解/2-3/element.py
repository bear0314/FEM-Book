import numpy as np

def get_element_nodes(model, e):
    """获取单元e两个节点坐标"""
    n1, n2 = model["IEN"][e]
    x1 = model["x"][n1]
    x2 = model["x"][n2]
    if model["nsd"] == 1:
        y1, y2 = 0, 0
    else:
        y1 = model["y"][n1]
        y2 = model["y"][n2]
    return (x1, y1), (x2, y2)

def compute_truss_ke(model, e):
    """计算1D/2D桁架单元刚度矩阵Ke"""
    E = model["E"][e]
    A = model["A"][e]
    (x1, y1), (x2, y2) = get_element_nodes(model, e)
    dx = x2 - x1
    dy = y2 - y1
    L = np.sqrt(dx**2 + dy**2)
    c = dx / L
    s = dy / L
    EA_L = E * A / L
    if model["nsd"] == 1:
        # 一维杆单元 Ke: 2x2
        Ke = EA_L * np.array([[1, -1], [-1, 1]])
    else:
        # 二维桁架 Ke:4x4
        Ke = EA_L * np.array([
            [c**2, c*s, -c**2, -c*s],
            [c*s, s**2, -c*s, -s**2],
            [-c**2, -c*s, c**2, c*s],
            [-c*s, -s**2, c*s, s**2]
        ])
    return Ke, L, c, s

def compute_truss_stress(model, e, de, L, c, s):
    """由单元位移de计算单元应力、轴力"""
    E = model["E"][e]
    A = model["A"][e]
    if model["nsd"] == 1:
        T = np.array([-1, 1])
    else:
        T = np.array([-c, -s, c, s])
    sigma = E / L * T @ de
    N = sigma * A
    return sigma, N

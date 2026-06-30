import numpy as np

def assemble_global_K(model, LM):
    """按LM对号矩阵组装总体刚度K"""
    ndof_tot = model["ndof_total"]
    K = np.zeros((ndof_tot, ndof_tot))
    nel = model["nel"]
    for e in range(nel):
        Ke, _, _, _ = compute_truss_ke(model, e)
        lm_e = LM[:, e]
        # 直接累加 K[i,j] += Ke[a,b]
        for a in range(len(lm_e)):
            for b in range(len(lm_e)):
                i = lm_e[a]
                j = lm_e[b]
                K[i, j] += Ke[a, b]
    return K

def check_symmetric(K, tol=1e-10):
    """检查刚度矩阵对称性"""
    diff = np.max(np.abs(K - K.T))
    is_sym = diff < tol
    print(f"矩阵对称误差max|K-KT|={diff:.2e}, 对称:{is_sym}")
    return is_sym

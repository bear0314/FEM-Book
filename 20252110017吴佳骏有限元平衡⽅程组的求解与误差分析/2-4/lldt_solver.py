import numpy as np
from numpy.linalg import norm

def ldlt_factor(K):
    """
    LDL^T分解 K = L @ D @ L.T
    :param K: 对称方阵 n×n
    :return: L(单位下三角), D(对角向量), flag(1成功/0非正定)
    """
    n = K.shape[0]
    L = np.eye(n, dtype=np.float64)
    D = np.zeros(n, dtype=np.float64)
    eps = 1e-12

    for j in range(n):
        s = 0.0
        for k in range(j):
            s += L[j, k] * D[k] * L[j, k]
        D[j] = K[j, j] - s

        if D[j] <= eps:
            print(f"【分解失败】主元D[{j}] = {D[j]:.2e} ≤ 0，矩阵非正定/存在零主元")
            return L, D, 0

        for i in range(j+1, n):
            s2 = 0.0
            for k in range(j):
                s2 += L[i, k] * D[k] * L[j, k]
            L[i, j] = (K[i, j] - s2) / D[j]
    return L, D, 1

def ldlt_solve(L, D, R):
    """三步求解 LDL^T a = R：前代→对角→回代"""
    n = len(R)
    # 前代 L y = R
    y = np.zeros(n)
    for i in range(n):
        s = 0.0
        for k in range(i):
            s += L[i, k] * y[k]
        y[i] = R[i] - s
    # 对角 D z = y
    z = y / D
    # 回代 L^T a = z
    a = np.zeros(n)
    for i in range(n-1, -1, -1):
        s = 0.0
        for k in range(i+1, n):
            s += L[k, i] * a[k]
        a[i] = z[i] - s
    return a

def residual_norm(K, a, R):
    """计算残差向量、残差2范数、相对残差"""
    r = R - K @ a
    norm_r = norm(r)
    norm_R = norm(R)
    rel_r = norm_r / norm_R if norm_R > 1e-16 else 0.0
    return r, norm_r, rel_r

def relative_error(a_num, a_exact):
    """数值解相对真解误差"""
    diff = a_num - a_exact
    norm_diff = norm(diff)
    norm_ex = norm(a_exact)
    return norm_diff / norm_ex if norm_ex > 1e-16 else 0.0

def matrix_cond(K):
    """对称矩阵2-范数条件数"""
    eig = np.linalg.eigvalsh(K)
    eig_abs = np.abs(eig)
    return np.max(eig_abs) / np.min(eig_abs)

def solve_equilibrium(K_FF, rhs, method="ldlt", **options):
    """统一求解接口"""
    if method == "ldlt":
        L, D, flag = ldlt_factor(K_FF)
        if flag == 0:
            raise ValueError("矩阵非正定，LDLT分解终止")
        a = ldlt_solve(L, D, rhs)
        r, nr, rrel = residual_norm(K_FF, a, rhs)
        return {
            "sol": a, "L": L, "D": D, "residual_vec": r,
            "norm_res": nr, "rel_residual": rrel, "flag": 1
        }
    elif method in ["scipy_sparse", "pardiso"]:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import spsolve
        K_sp = csr_matrix(K_FF)
        a = spsolve(K_sp, rhs)
        r, nr, rrel = residual_norm(K_FF, a, rhs)
        return {
            "sol": a, "norm_res": nr, "rel_residual": rrel, "flag": 1
        }
    else:
        raise NotImplementedError(f"不支持求解方法 {method}")

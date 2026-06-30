import numpy as np

def solve_reduction(K, f, model):
    """缩减法求解：K_FF dF = fF - K_EF^T dE"""
    ndof_tot = model["ndof_total"]
    fixed_dofs = model["fixed_dof"]
    fixed_vals = model["fixed_val"]
    # 划分自由F/约束E自由度
    all_dofs = np.arange(ndof_tot)
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs)
    # 构建映射
    d = np.zeros(ndof_tot)
    d[fixed_dofs] = fixed_vals
    # 分块矩阵
    K_FF = K[np.ix_(free_dofs, free_dofs)]
    K_EF = K[np.ix_(fixed_dofs, free_dofs)]
    f_F = f[free_dofs]
    d_E = d[fixed_dofs]
    # 右端项
    rhs = f_F - K_EF.T @ d_E
    # 求解自由位移
    d_F = np.linalg.solve(K_FF, rhs)
    d[free_dofs] = d_F
    # 计算约束反力 R_E = K_EF dF + K_EE d_E - f_E
    K_EE = K[np.ix_(fixed_dofs, fixed_dofs)]
    f_E = f[fixed_dofs]
    R_E = K_EF @ d_F + K_EE @ d_E - f_E
    return d, free_dofs, fixed_dofs, R_E, K_FF

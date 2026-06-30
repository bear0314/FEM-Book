# 新增：屏蔽matplotlib字体缺失UserWarning
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import numpy as np
import time
from lldt_solver import *
from truss_fea_23 import TrussFEA23
from sparse_solver_wrapper import build_tridiag_sparse, sparse_solve
from poisson_fem_q4 import poisson_fem_assemble, poisson_postprocess

def case0_truss_1d_two_elem():
    """算例0：一维两单元杆结构（2.3衔接算例，修复节点解包错误）"""
    print("===== 算例0：一维两单元杆结构 =====")
    E, A = 100, 1.0
    fea = TrussFEA23(E, A)
    # 修复：二维[x,y]节点，不再一维列表
    nodes = [
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0]
    ]
    elems = [[0, 1], [1, 2]]
    fea.set_model(nodes, elems)
    fea.assemble_global()
    # 完整边界约束，避免刚体位移
    bc = {0:0.0, 1:0.0, 3:0.0, 5:0.0}
    load = {4:10.0}
    fea.apply_bc_load(bc, load)
    sol_res = solve_equilibrium(fea.K_FF, fea.rhs, method="ldlt")
    d_F = sol_res["sol"]
    print("自由位移d_F：", d_F)
    d_full = fea.reconstruct_full_disp(d_F)
    print("完整节点位移：", d_full)
    react = fea.calc_reaction(d_full)
    print("约束反力：", react)
    elem_res = fea.calc_elem_force_stress(d_full)
    for e in elem_res:
        print(f"单元{e['elem_idx']} 轴力={e['force']:.4f}, 应力={e['stress']:.4f}")
    fea.export_json("truss_1d.json")
    return sol_res

def case1_ill_condition_matrix():
    """算例1：病态矩阵残差与误差分析"""
    print("\n===== 算例1：病态矩阵残差与误差分析 =====")
    K = np.array([[1.0, 1.0], [1.0, 1.0001]])
    a_ex = np.array([1.0, 1.0])
    R = K @ a_ex
    cond = matrix_cond(K)
    print(f"矩阵条件数 cond(K) = {cond:.2e}")
    L, D, flag = ldlt_factor(K)
    a_double = ldlt_solve(L, D, R)
    r_d, nr_d, rrel_d = residual_norm(K, a_double, R)
    err_d = relative_error(a_double, a_ex)
    print("【双精度】")
    print(f"解a={a_double}, ||r||={nr_d:.2e}, 相对残差={rrel_d:.2e}, 相对误差={err_d:.2e}")
    def round4(x):
        return np.round(x, 4-int(np.floor(np.log10(np.abs(x))+1e-12)))
    K_4 = np.vectorize(round4)(K)
    R_4 = np.vectorize(round4)(R)
    L4, D4, f4 = ldlt_factor(K_4)
    a_4 = ldlt_solve(L4, D4, R_4)
    r4, nr4, rrel4 = residual_norm(K_4, a_4, R)
    err4 = relative_error(a_4, a_ex)
    print("【4位有效数字截断模拟低精度】")
    print(f"解a={a_4}, ||r||={nr4:.2e}, 相对残差={rrel4:.2e}, 相对误差={err4:.2e}")
    print("结论：病态矩阵残差小，但解的误差被条件数放大")

def case2_non_positive_definite():
    """算例2：非正定矩阵检测"""
    print("\n===== 算例2：非正定矩阵检测 =====")
    K = np.array([[1, 2], [2, 1]])
    R = np.array([1,1])
    L, D, flag = ldlt_factor(K)
    print("分解flag(1成功/0失败) =", flag)
    print("D对角向量：", D)

def case3_tridiag_scale_test():
    """算例3：不同规模三对角稠密/稀疏求解效率对比"""
    print("\n===== 算例3：三对角矩阵规模效率测试 =====")
    for n in [10, 100, 500]:
        K_sp, rhs, a_ex = build_tridiag_sparse(n)
        K_d = K_sp.todense()
        t0 = time.time()
        L,D,f = ldlt_factor(K_d)
        a_d = ldlt_solve(L,D,rhs)
        t_d = time.time()-t0
        err_d = relative_error(a_d, a_ex)
        t0 = time.time()
        sres = sparse_solve(K_sp, rhs, solver="scipy")
        t_s = time.time()-t0
        a_s = sres["sol"]
        err_s = relative_error(a_s, a_ex)
        print(f"n={n:3d} | 稠密LDLT耗时{t_d:.4f}s 误差{err_d:.2e} | 稀疏spsolve耗时{t_s:.4f}s 误差{err_s:.2e}")

def case4_poisson_fem(nx=20, ny=20):
    """算例4：Poisson方程Q4有限元求解与误差绘图"""
    print(f"\n===== 算例4：Poisson方程 Q4网格 nx={nx}, ny={ny} =====")
    res = poisson_fem_assemble(nx, ny)
    print(f"单元总数={nx*ny}, 总节点={res['n_node']}, 自由自由度={len(res['free_dof'])}")
    print(f"网格装配耗时={res['t_assemble']:.4f}s")
    sres = sparse_solve(res["Kff"], res["Ff"], solver="scipy")
    print(f"求解器:{sres['solver_name']}, 求解耗时={sres['solve_time']:.4f}s, 矩阵非零元数量={sres['nnz']}")
    post = poisson_postprocess(res, sres["sol"])
    print(f"节点最大误差={post['max_error']:.2e}, 离散L2相对误差={post['rel_L2']:.2e}")

if __name__ == "__main__":
    case0_truss_1d_two_elem()
    case1_ill_condition_matrix()
    case2_non_positive_definite()
    case3_tridiag_scale_test()
    case4_poisson_fem(nx=20, ny=20)

import json
import numpy as np

# ========== 前处理函数（原model.py） ==========
def read_model(json_path):
    """读取JSON输入文件，统一转换为0下标"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    model = {}
    model["nsd"] = data["nsd"]
    model["ndof"] = data["ndof"]
    model["nnp"] = data["nnp"]
    model["nel"] = data["nel"]
    model["nen"] = data["nen"]
    model["E"] = np.array(data["E"], dtype=float)
    model["A"] = np.array(data["CArea"], dtype=float)
    model["x"] = np.array(data["x"], dtype=float)
    model["y"] = np.array(data["y"], dtype=float) if model["nsd"] >=2 else None
    IEN_1 = np.array(data["IEN"], dtype=int)
    model["IEN"] = IEN_1 - 1
    fixed_dof_1 = np.array(data["fixed_dof"], dtype=int)
    model["fixed_dof"] = fixed_dof_1 - 1
    model["fixed_val"] = np.array(data["fixed_value"], dtype=float)
    force_dof_1 = np.array(data["force_dof"], dtype=int)
    model["force_dof"] = force_dof_1 - 1
    model["force_val"] = np.array(data["force_value"], dtype=float)
    model["ndof_total"] = model["nnp"] * model["ndof"]
    return model

def build_LM(model):
    nel = model["nel"]
    nen = model["nen"]
    ndof = model["ndof"]
    LM = np.zeros((nen * ndof, nel), dtype=int)
    for e in range(nel):
        n1, n2 = model["IEN"][e]
        for d in range(ndof):
            LM[d, e] = n1 * ndof + d
        for d in range(ndof):
            LM[ndof + d, e] = n2 * ndof + d
    return LM

def init_force_vector(model):
    ndof_tot = model["ndof_total"]
    f = np.zeros(ndof_tot)
    for dof, val in zip(model["force_dof"], model["force_val"]):
        f[dof] = val
    return f

# ========== 单元刚度函数（原element.py） ==========
def get_element_nodes(model, e):
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
        Ke = EA_L * np.array([[1, -1], [-1, 1]])
    else:
        Ke = EA_L * np.array([
            [c**2, c*s, -c**2, -c*s],
            [c*s, s**2, -c*s, -s**2],
            [-c**2, -c*s, c**2, c*s],
            [-c*s, -s**2, c*s, s**2]
        ])
    return Ke, L, c, s

def compute_truss_stress(model, e, de, L, c, s):
    E = model["E"][e]
    A = model["A"][e]
    if model["nsd"] == 1:
        T = np.array([-1, 1])
    else:
        T = np.array([-c, -s, c, s])
    sigma = E / L * T @ de
    N = sigma * A
    return sigma, N

# ========== 总体刚度组装（原assembly.py） ==========
def assemble_global_K(model, LM):
    ndof_tot = model["ndof_total"]
    K = np.zeros((ndof_tot, ndof_tot))
    nel = model["nel"]
    for e in range(nel):
        Ke, _, _, _ = compute_truss_ke(model, e)
        lm_e = LM[:, e]
        for a in range(len(lm_e)):
            for b in range(len(lm_e)):
                i = lm_e[a]
                j = lm_e[b]
                K[i, j] += Ke[a, b]
    return K

def check_symmetric(K, tol=1e-10):
    diff = np.max(np.abs(K - K.T))
    is_sym = diff < tol
    print(f"矩阵对称误差max|K-KT|={diff:.2e}, 对称:{is_sym}")
    return is_sym

# ========== 求解模块（原solver.py） ==========
def solve_reduction(K, f, model):
    ndof_tot = model["ndof_total"]
    fixed_dofs = model["fixed_dof"]
    fixed_vals = model["fixed_val"]
    all_dofs = np.arange(ndof_tot)
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs)
    d = np.zeros(ndof_tot)
    d[fixed_dofs] = fixed_vals
    K_FF = K[np.ix_(free_dofs, free_dofs)]
    K_EF = K[np.ix_(fixed_dofs, free_dofs)]
    f_F = f[free_dofs]
    d_E = d[fixed_dofs]
    rhs = f_F - K_EF.T @ d_E
    d_F = np.linalg.solve(K_FF, rhs)
    d[free_dofs] = d_F
    K_EE = K[np.ix_(fixed_dofs, fixed_dofs)]
    f_E = f[fixed_dofs]
    R_E = K_EF @ d_F + K_EE @ d_E - f_E
    return d, free_dofs, fixed_dofs, R_E, K_FF

# ========== 后处理模块（原postprocess.py） ==========
def postprocess_all_elements(model, LM, d):
    nel = model["nel"]
    elem_results = []
    print("\n===== 单元后处理结果 =====")
    for e in range(nel):
        lm_e = LM[:, e]
        de = d[lm_e]
        Ke, L, c, s = compute_truss_ke(model, e)
        sigma, N = compute_truss_stress(model, e, de, L, c, s)
        res = {
            "elem_id": e+1,
            "L": L,
            "c": c,
            "s": s,
            "sigma": sigma,
            "N": N
        }
        elem_results.append(res)
        print(f"单元{e+1}: L={L:.6f}, c={c:.6f}, s={s:.6f}, 应力={sigma:.6f}, 轴力={N:.6f}")
    return elem_results

# ========== 算例运行主函数 ==========
def run_case(json_path, case_name):
    print("="*60)
    print(f"开始计算算例: {case_name}")
    print("="*60)
    model = read_model(json_path)
    LM = build_LM(model)
    f = init_force_vector(model)
    print(f"\n对号矩阵LM(shape={LM.shape}):\n{LM}")
    K = assemble_global_K(model, LM)
    print(f"\n总体刚度矩阵K:\n{np.round(K,4)}")
    check_symmetric(K)
    eig_vals = np.linalg.eigvals(K)
    min_eig = np.min(np.abs(eig_vals))
    print(f"组装前刚度矩阵最小特征值|λ|={min_eig:.2e}, 奇异判定:{min_eig<1e-8}")
    d, free_dofs, fixed_dofs, R_E, K_FF = solve_reduction(K, f, model)
    print(f"\n全局位移向量d:\n{np.round(d,6)}")
    print(f"\n约束自由度编号(0下标):{fixed_dofs}")
    print(f"约束反力:\n{np.round(R_E,6)}")
    eig_ff = np.linalg.eigvals(K_FF)
    min_eig_ff = np.min(np.abs(eig_ff))
    print(f"缩减矩阵K_FF最小特征值|λ|={min_eig_ff:.2e}, 奇异判定:{min_eig_ff<1e-8}")
    postprocess_all_elements(model, LM, d)
    print("="*60 + "\n")
    return model, K, d, R_E

# ========== 程序执行入口（必须保留，否则无输出） ==========
if __name__ == "__main__":
    run_case("case1_1d.json", "一维两单元杆算例")
    run_case("case2_2d.json", "二维两杆桁架算例")

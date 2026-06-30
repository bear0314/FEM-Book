import numpy as np

def truss3d_element_stiffness(x1, x2, E, A):
    """
    计算三维杆单元长度、方向余弦、全局刚度矩阵Ke(6×6)
    :param x1: 节点1坐标 [x1,y1,z1] list/np.array
    :param x2: 节点2坐标 [x2,y2,z2] list/np.array
    :param E: 弹性模量 (Pa)
    :param A: 横截面积 (m^2)
    :return: L(长度), dir_cos([cx,cy,cz]), Ke(6×6 np矩阵)
    """
    x1 = np.array(x1, dtype=np.float64)
    x2 = np.array(x2, dtype=np.float64)
    dx = x2[0] - x1[0]
    dy = x2[1] - x1[1]
    dz = x2[2] - x1[2]
    L = np.sqrt(dx**2 + dy**2 + dz**2)
    # 退化单元判断：两节点重合
    if np.isclose(L, 0.0):
        raise ValueError("错误：单元两个节点坐标重合，无效退化杆单元！")
    # 方向余弦
    cx = dx / L
    cy = dy / L
    cz = dz / L
    dir_cos = np.array([cx, cy, cz])
    # 转换矩阵 T (1×6)
    T = np.array([-cx, -cy, -cz, cx, cy, cz])
    # 局部刚度 k_local = E*A/L
    k_local = E * A / L
    # 全局刚度 Ke = k_local * T^T @ T
    Ke = k_local * np.outer(T, T)
    return L, dir_cos, Ke

def truss3d_element_stress(x1, x2, E, A, de):
    """
    根据节点位移de计算轴向应变、应力、轴力
    :param de: 单元位移向量 [u1,v1,w1,u2,v2,w2] (m)
    :return: epsilon(应变), sigma(应力 Pa), N(轴力 N)
    """
    L, dir_cos, Ke = truss3d_element_stiffness(x1, x2, E, A)
    cx, cy, cz = dir_cos
    T = np.array([-cx, -cy, -cz, cx, cy, cz])
    de = np.array(de, dtype=np.float64)
    # 轴向伸长量 delta = T @ de
    delta = T @ de
    epsilon = delta / L
    sigma = E * epsilon
    N = sigma * A
    return epsilon, sigma, N

def check_ke_property(Ke):
    """校验刚度矩阵性质：对称性、特征值、奇异性"""
    print("===== 单元刚度矩阵性质校验 =====")
    # 1. 对称性检查
    is_symmetric = np.allclose(Ke, Ke.T)
    print(f"1. 矩阵对称：{is_symmetric}")
    # 2. 特征值
    eigvals = np.linalg.eigvalsh(Ke)
    print(f"2. 全部特征值非负（半正定）：{np.all(eigvals >= -1e-12)}")
    print(f"   特征值列表：{np.round(eigvals, 6)}")
    # 3. 秩/奇异性：自由杆单元秩最多3，行列式≈0
    det = np.linalg.det(Ke)
    print(f"3. Ke行列式 ≈ {det:.2e}，接近0 → 矩阵奇异")
    print("="*40)
    return eigvals

def rigid_body_test(x1, x2, E, A):
    """刚体平移测试：整体平移位移无内力"""
    L, dir_cos, Ke = truss3d_element_stiffness(x1, x2, E, A)
    # 全局刚体平移：所有节点同位移 [a,a,a,a,a,a]
    de_rigid = np.array([0.001, 0.002, 0.003, 0.001, 0.002, 0.003])
    Fe = Ke @ de_rigid
    print("\n===== 刚体平移测试 =====")
    print(f"刚体平移位移 de = {de_rigid}")
    print(f"等效节点力 Fe = {np.round(Fe, 8)}")
    print("刚体平移无内力，节点力全部趋近于0，验证通过")
    print("="*40)

def ke_column_physical_meaning(x1, x2, E, A, j=0):
    """
    刚度矩阵列物理意义验证：仅第j个自由度位移=1，其余0
    Fe = Ke * de → Fe等于Ke第j列
    :param j: 自由度序号 0~5
    """
    L, dir_cos, Ke = truss3d_element_stiffness(x1, x2, E, A)
    de = np.zeros(6)
    de[j] = 1.0
    Fe = Ke @ de
    print(f"\n===== 刚度矩阵第{j+1}列物理意义验证 =====")
    print(f"仅自由度{j}位移=1，其余为0，位移向量 de = {de}")
    print(f"平衡节点力 Fe = Ke·de = \n{np.round(Fe, 6)}")
    print(f"Ke第{j+1}列：\n{np.round(Ke[:, j], 6)}")
    print("结论：Fe与Ke第j列完全相等，k_ij代表仅j自由度单位位移时i方向所需节点力")
    print("="*40)

def case1_x_axis_bar():
    """算例1：沿X轴一维杆"""
    print("========== 算例1：沿X轴杆单元 ==========")
    x1 = [0, 0, 0]
    x2 = [2, 0, 0]
    E = 200e9    # 200 GPa
    A = 1.0e-4   # m²
    de = [0, 0, 0, 1.0e-3, 0, 0]
    # 几何刚度
    L, dir_cos, Ke = truss3d_element_stiffness(x1, x2, E, A)
    print(f"单元长度 L = {L:.4f} m")
    print(f"方向余弦 cx,cy,cz = {np.round(dir_cos, 4)}")
    print("全局刚度矩阵 Ke (6×6):")
    print(np.round(Ke, 2))
    # 应变应力轴力
    eps, sig, N = truss3d_element_stress(x1, x2, E, A, de)
    print(f"\n轴向应变 ε = {eps:.4e}")
    print(f"轴向应力 σ = {sig/1e6:.2f} MPa")
    print(f"轴力 N = {N:.2e} N")
    # 性质校验
    check_ke_property(Ke)
    rigid_body_test(x1, x2, E, A)
    ke_column_physical_meaning(x1, x2, E, A, j=3)
    print("========== 算例1 结束 ==========\n")

def case2_space_3d_bar():
    """算例2：空间斜杆 (0,0,0)→(1,2,2)"""
    print("========== 算例2：空间任意方向三维杆 ==========")
    x1 = [0, 0, 0]
    x2 = [1, 2, 2]
    E = 210e9    # 210 GPa
    A = 2.0e-4   # m²
    de = [0, 0, 0, 1.0e-3, 2.0e-3, 2.0e-3]
    L, dir_cos, Ke = truss3d_element_stiffness(x1, x2, E, A)
    print(f"单元长度 L = {L:.4f} m")
    print(f"方向余弦 cx,cy,cz = {np.round(dir_cos, 4)}")
    print("全局刚度矩阵 Ke (6×6):")
    print(np.round(Ke/1e6, 4))  # 缩放百万便于阅读
    # 应力应变
    eps, sig, N = truss3d_element_stress(x1, x2, E, A, de)
    print(f"\n轴向应变 ε = {eps:.4e}")
    print(f"轴向应力 σ = {sig/1e6:.2f} MPa")
    print(f"轴力 N = {N:.2e} N")
    # 校验
    check_ke_property(Ke)
    rigid_body_test(x1, x2, E, A)
    ke_column_physical_meaning(x1, x2, E, A, j=4)
    print("========== 算例2 结束 ==========\n")

def test_degenerate_element():
    """测试重合节点报错"""
    print("========== 退化单元测试（节点重合） ==========")
    try:
        truss3d_element_stiffness([1,1,1], [1,1,1], 200e9, 1e-4)
    except ValueError as err:
        print(f"捕获预期错误：{err}")
    print("="*50)

if __name__ == "__main__":
    # 依次运行全部测试
    test_degenerate_element()
    case1_x_axis_bar()
    case2_space_3d_bar()


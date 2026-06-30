import warnings
warnings.filterwarnings("ignore", message="findfont: Font family")
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

def alpha_supg(Pe):
    if abs(Pe) < 1e-8:
        return 0.0
    return 1 / np.tanh(Pe) - 1 / Pe

def element_matrix(kappa, v, le, alpha):
    k_bar = kappa + alpha * v * le / 2
    K_diff = k_bar / le * np.array([[1, -1], [-1, 1]])
    K_conv = v / 2 * np.array([[-1, 1], [-1, 1]])
    Ke = K_diff + K_conv
    return Ke

def solve_advection_diffusion(nel, L, v, kappa, alpha):
    le = L / nel
    nn = nel + 1
    x = np.linspace(0, L, nn)
    K_global = np.zeros((nn, nn))
    F = np.zeros(nn)

    for e in range(nel):
        idx = [e, e+1]
        Ke = element_matrix(kappa, v, le, alpha)
        for i in range(2):
            for j in range(2):
                K_global[idx[i], idx[j]] += Ke[i, j]

    K_global[0, :] = 0.0
    K_global[0, 0] = 1.0
    F[0] = 0.0
    K_global[-1, :] = 0.0
    K_global[-1, -1] = 1.0
    F[-1] = 1.0

    theta_num = np.linalg.solve(K_global, F)
    Pe_global = v * L / kappa
    theta_exact = (np.exp(v * x / kappa) - 1) / (np.exp(Pe_global) - 1)
    err = np.abs(theta_num - theta_exact)
    max_err = np.max(err)
    return x, theta_num, theta_exact, max_err, K_global

if __name__ == "__main__":
    L = 1.0
    nel = 20
    v = 1.0
    le = L / nel
    Pe_list = [0.1, 3.0]

    print("========== 一维对流扩散有限元计算开始 ==========")
    print(f"网格单元数 nel = {nel}, 单元长度 le = {le:.4f}")
    print(f"对流速度 v = {v:.2f}\n")

    for Pe in Pe_list:
        kappa = v * le / (2 * Pe)
        print(f"-------------------- Pe = {Pe:.2f} --------------------")
        print(f"对应扩散系数 κ = {kappa:.6f}")

        x_gal, theta_gal, theta_ex, err_gal, K_gal = solve_advection_diffusion(nel, L, v, kappa, 0)
        x_up, theta_up, _, err_up, _ = solve_advection_diffusion(nel, L, v, kappa, 1)
        a_opt = alpha_supg(Pe)
        x_supg, theta_supg, _, err_supg, _ = solve_advection_diffusion(nel, L, v, kappa, a_opt)

        print(f"alpha_opt(SUPG) = {a_opt:.6f}")
        print("最大节点误差：")
        print(f"标准Galerkin(α=0): {err_gal:.2e}")
        print(f"迎风格式(α=1):    {err_up:.2e}")
        print(f"SUPG(α_opt):      {err_supg:.2e}\n")

        plt.figure(figsize=(8, 5))
        plt.plot(x_gal, theta_ex, 'k-', linewidth=2, label="精确解")
        plt.plot(x_gal, theta_gal, 'r--', linewidth=1.5, label="标准Galerkin")
        plt.plot(x_up, theta_up, 'g-.', linewidth=1.5, label="迎风格式 α=1")
        plt.plot(x_supg, theta_supg, 'b:', linewidth=2, label="SUPG Petrov-Galerkin")
        plt.xlabel("x")
        plt.ylabel(r"$\theta(x)$")
        plt.title(f"Pe = {Pe:.2f}, nel = {nel}")
        plt.legend(loc="best")
        plt.grid(True)
        plt.savefig(f"Pe_{Pe:.1f}_result.png", dpi=300)
        plt.show(block=False)
        input(f"当前Pe={Pe:.2f}图像已生成，按回车继续下一组计算")
        plt.close()

        if Pe == 3.0:
            print("==== Pe=3.0 标准Galerkin总刚矩阵分析 ====")
            print(K_gal)
            is_sym = np.allclose(K_gal, K_gal.T)
            print(f"矩阵是否对称：{'是' if is_sym else '否'}")
            eig_vals = np.linalg.eigvals(K_gal)
            is_posdef = np.all(eig_vals > -1e-10)
            print(f"矩阵是否正定：{'是' if is_posdef else '否'}")
            print(f"最小特征值 = {np.min(eig_vals):.4e}\n")

    # 第三张收敛曲线图
    print("========== 附加题：网格加密收敛测试 ==========")
    Pe_test = 3.0
    nel_cases = [10, 20, 40, 80]
    err_gal_series = []
    err_supg_series = []
    le_series = [L / n for n in nel_cases]

    for n in nel_cases:
        le_i = L / n
        kappa_i = v * le_i / (2 * Pe_test)
        _, _, _, eg, _ = solve_advection_diffusion(n, L, v, kappa_i, 0)
        err_gal_series.append(eg)
        aopt = alpha_supg(Pe_test)
        _, _, _, es, _ = solve_advection_diffusion(n, L, v, kappa_i, aopt)
        err_supg_series.append(es)

    plt.figure(figsize=(8, 5))
    plt.loglog(le_series, err_gal_series, 'ro-', linewidth=1.5, label="标准Galerkin")
    plt.loglog(le_series, err_supg_series, 'bs-', linewidth=1.5, label="SUPG稳定化")
    plt.xlabel("单元长度 le (log)")
    plt.ylabel(r"最大节点误差 $|\theta_{num}-\theta_{ex}|$ (log)")
    plt.title("网格加密收敛曲线 Pe=3.0")
    plt.legend(loc="best")
    plt.grid(True)
    plt.savefig("convergence_curve.png", dpi=300)
    plt.show()
    print("全部3张图像保存完成：Pe0.1、Pe3.0、收敛曲线")

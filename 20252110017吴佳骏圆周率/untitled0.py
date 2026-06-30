import matplotlib.pyplot as plt
import numpy as np
import warnings
from scipy.interpolate import interp1d

# ========== 全局配置：解决中文乱码、屏蔽字体警告 ==========
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False
warnings.filterwarnings("ignore", category=UserWarning)

# 1. 原始割圆逼近数据
n = [1, 2, 4, 8, 16, 32, 64, 128, 256]
pi_n = [
    0,
    2.0,
    2.828427124746190,
    3.061467458920718,
    3.121445152258052,
    3.136548490545939,
    3.140331156954753,
    3.141277250932773,
    3.141513801144301
]
pi_exact = np.pi
h = np.array([1/x for x in n])
e_n = np.abs(pi_exact - np.array(pi_n))

# 2. Wynn外插数据
extrapolated_data = {
    4: 3.414213562373096,
    16: 3.141418327933211,
    64: 3.141592658918053,
    256: 3.141592653589786
}
h_ext = np.array([1/x for x in extrapolated_data.keys()])
pi_ext = np.array(list(extrapolated_data.values()))
e_ext = np.abs(pi_exact - pi_ext)

# ========== 生成平滑曲线（延伸至h=1，末端相交） ==========
log_h_full = np.linspace(np.log10(1e-3), np.log10(1), 400)
h_full = 10 ** log_h_full

# 蓝色原始曲线插值
log_h_ori = np.log10(h)
log_e_ori = np.log10(e_n)
f_ori = interp1d(log_h_ori, log_e_ori, kind="linear", fill_value="extrapolate")
log_e_ori_smooth = f_ori(log_h_full)
e_ori_smooth = 10 ** log_e_ori_smooth

# 红色外插三次平滑插值
log_h_ext_log = np.log10(h_ext)
log_e_ext_log = np.log10(e_ext)
f_ext = interp1d(log_h_ext_log, log_e_ext_log, kind="cubic", fill_value="extrapolate")
log_e_ext_smooth = f_ext(log_h_full)
e_ext_smooth = 10 ** log_e_ext_smooth

# 3. 绘图
plt.figure(figsize=(12, 9), dpi=100)
# 平滑连续曲线
plt.loglog(h_full, e_ori_smooth, "b-", linewidth=2)
plt.loglog(h_full, e_ext_smooth, "r-", linewidth=2)
# 离散标记点：蓝色三角、红色方块
plt.loglog(h, e_n, 'b^', markersize=8, label=r'多边形逼近 $\pi_n$')
plt.loglog(h_ext, e_ext, 'rs', markersize=8, label=r'Wynn-$\epsilon$ 外推')

# 修复yticks：5个刻度对应5个标签，修正10^5语法错误
plt.xticks([1e-3, 1e-2, 1e-1, 1], labels=['$10^{-3}$', '$10^{-2}$', '$10^{-1}$', '$10^{0}$'])
plt.yticks(
    [1e-15, 1e-10, 1e-5, 1e0, 1e5],
    labels=['$10^{-15}$', '$10^{-10}$', '$10^{-5}$', '$10^{0}$', '$10^{5}$']
)

plt.xlim(1e-3, 1)
plt.ylim(1e-16, 1e5)
plt.xlabel(r'$h=1/n$', fontsize=13)
plt.ylabel(r'$e_n=|\pi-\pi_n|$', fontsize=13)
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend(fontsize=12)
plt.title('割圆术误差双对数曲线（含完整外插点）', fontsize=14)

# 计算并标注收敛阶
# 原始逼近斜率（过滤n=1无效点）
valid_idx = e_n != 0
lg_h_valid = np.log10(h[valid_idx])
lg_e_valid = np.log10(e_n[valid_idx])
k_original, _ = np.polyfit(lg_h_valid, lg_e_valid, 1)
# 外插斜率
lg_hext = np.log10(h_ext)
lg_eext = np.log10(e_ext)
k_extrap, _ = np.polyfit(lg_hext, lg_eext, 1)

# 图内标注收敛阶文字
plt.text(0.02, 1e-3, f"收敛阶: {k_original:.4f}", color="blue", fontsize=14)
plt.text(0.02, 1e-6, f"收敛阶: {k_extrap:.4f}", color="red", fontsize=14)

plt.tight_layout()
plt.show()

# 控制台输出收敛阶
print(f"多边形逼近误差斜率（收敛阶）: {k_original:.4f}")
print(f"Wynn外插误差斜率（收敛阶）: {k_extrap:.4f}")

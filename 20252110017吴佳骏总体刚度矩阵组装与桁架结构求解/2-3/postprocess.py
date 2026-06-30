import numpy as np

def postprocess_all_elements(model, LM, d):
    """遍历所有单元，输出长度、方向余弦、应力、轴力"""
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

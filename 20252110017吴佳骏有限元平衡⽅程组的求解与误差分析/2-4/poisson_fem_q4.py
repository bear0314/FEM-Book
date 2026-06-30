import numpy as np
import matplotlib.pyplot as plt
# 新增：解决中文/特殊符号字体缺失警告
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
from scipy.sparse import dok_matrix
from sparse_solver_wrapper import sparse_solve
import time

def shape_q4(xi, eta):
    N = 0.25 * np.array([
        (1-xi)*(1-eta),
        (1+xi)*(1-eta),
        (1+xi)*(1+eta),
        (1-xi)*(1+eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1-eta), (1-eta), (1+eta), -(1+eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1-xi), -(1+xi), (1+xi), (1-xi)
    ])
    return N, dNdxi, dNdeta

def elem_stiff_q4(x_nodes, y_nodes):
    gauss = np.array([[-1/np.sqrt(3), -1/np.sqrt(3)],
                      [ 1/np.sqrt(3), -1/np.sqrt(3)],
                      [ 1/np.sqrt(3),  1/np.sqrt(3)],
                      [-1/np.sqrt(3),  1/np.sqrt(3)]])
    weights = np.ones(4)
    Ke = np.zeros((4,4))
    fe = np.zeros(4)
    for gp, w in zip(gauss, weights):
        xi, eta = gp
        N, dNdxi, dNdeta = shape_q4(xi, eta)
        dx_dxi = np.sum(dNdxi * x_nodes)
        dx_deta = np.sum(dNdeta * x_nodes)
        dy_dxi = np.sum(dNdxi * y_nodes)
        dy_deta = np.sum(dNdeta * y_nodes)
        J = np.array([[dx_dxi, dx_deta], [dy_dxi, dy_deta]])
        detJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        dNdxdy = invJ @ np.vstack([dNdxi, dNdeta])
        dNdx, dNdy = dNdxdy[0,:], dNdxdy[1,:]
        for i in range(4):
            for j in range(4):
                Ke[i,j] += (dNdx[i]*dNdx[j] + dNdy[i]*dNdy[j]) * detJ * w
        x = np.sum(N * x_nodes)
        y = np.sum(N * y_nodes)
        f_val = 2 * np.pi**2 * np.sin(np.pi*x) * np.sin(np.pi*y)
        for i in range(4):
            fe[i] += N[i] * f_val * detJ * w
    return Ke, fe

def poisson_fem_assemble(nx, ny):
    hx = 1.0 / nx
    hy = 1.0 / ny
    nnx = nx + 1
    nny = ny + 1
    n_node = nnx * nny
    node_coords = np.zeros((n_node, 2))
    for j in range(nny):
        for i in range(nnx):
            idx = j * nnx + i
            node_coords[idx] = [i*hx, j*hy]
    elem_dof = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * nnx + i
            n1 = n0 + 1
            n2 = n0 + nnx + 1
            n3 = n0 + nnx
            elem_dof.append([n0, n1, n2, n3])
    K_dok = dok_matrix((n_node, n_node), dtype=np.float64)
    F = np.zeros(n_node)
    t_assemble = time.time()
    for edof in elem_dof:
        xy = node_coords[edof]
        x_e = xy[:,0]
        y_e = xy[:,1]
        Ke, fe = elem_stiff_q4(x_e, y_e)
        for i in range(4):
            F[edof[i]] += fe[i]
            for j in range(4):
                K_dok[edof[i], edof[j]] += Ke[i,j]
    t_assemble = time.time() - t_assemble
    bc_dof = []
    for j in range(nny):
        for i in range(nnx):
            x, y = node_coords[j*nnx+i]
            if x < 1e-12 or x > 1-1e-12 or y <1e-12 or y>1-1e-12:
                bc_dof.append(j*nnx+i)
    free_dof = [d for d in range(n_node) if d not in bc_dof]
    K_sp = K_dok.tocsr()
    Kff = K_sp[free_dof,:][:,free_dof]
    Ff = F[free_dof]
    return {
        "Kff": Kff, "Ff": Ff, "node_coords": node_coords,
        "nnx": nnx, "nny": nny, "n_node": n_node,
        "free_dof": free_dof, "bc_dof": bc_dof,
        "t_assemble": t_assemble, "nx": nx, "ny": ny
    }

def poisson_exact(x, y):
    return np.sin(np.pi * x) * np.sin(np.pi * y)

def poisson_postprocess(res, sol_vec):
    full_u = np.zeros(res["n_node"])
    full_u[res["free_dof"]] = sol_vec
    x = res["node_coords"][:,0]
    y = res["node_coords"][:,1]
    u_ex = poisson_exact(x, y)
    max_err = np.max(np.abs(full_u - u_ex))
    l2_num = np.linalg.norm(full_u - u_ex)
    l2_ex = np.linalg.norm(u_ex)
    rel_l2 = l2_num / l2_ex
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(12,5))
    nnx, nny = res["nnx"], res["nny"]
    U_num = full_u.reshape(nny, nnx)
    U_ex = u_ex.reshape(nny, nnx)
    im1 = ax1.imshow(U_num, origin="lower", extent=[0,1,0,1], cmap="jet")
    ax1.set_title("数值解 u_h")
    plt.colorbar(im1, ax=ax1)
    im2 = ax2.imshow(np.abs(U_num-U_ex), origin="lower", extent=[0,1,0,1], cmap="jet")
    ax2.set_title("误差 |u_h - u_ex|")
    plt.colorbar(im2, ax=ax2)
    plt.tight_layout()
    plt.savefig(f"poisson_nx{res['nx']}_ny{res['ny']}.png", dpi=150)
    plt.show()
    return {"max_error": max_err, "rel_L2": rel_l2, "u_num": full_u, "u_ex": u_ex}

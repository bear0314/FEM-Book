import numpy as np
import time
from scipy.sparse import coo_matrix, csr_matrix, dok_matrix
from scipy.sparse.linalg import spsolve
try:
    from pypardiso import PyPardisoSolver
    PYPARDISO_AVAIL = True
except ImportError:
    PYPARDISO_AVAIL = False
    print("警告：未安装pypardiso，仅可用scipy spsolve")

def dense2sparse(K_dense, fmt="csr"):
    coo = coo_matrix(K_dense)
    if fmt == "coo":
        return coo
    elif fmt == "csr":
        return coo.tocsr()
    else:
        raise ValueError("fmt only coo/csr")

def sparse_solve(K_sp, rhs, solver="scipy"):
    t0 = time.time()
    if solver == "scipy":
        sol = spsolve(K_sp, rhs)
    elif solver == "pardiso":
        if not PYPARDISO_AVAIL:
            raise RuntimeError("pypardiso未安装")
        ps = PyPardisoSolver(mtype=2)
        sol = ps.solve(K_sp, rhs)
    else:
        raise NotImplementedError
    t_solve = time.time() - t0
    nnz = K_sp.nnz
    n = K_sp.shape[0]
    return {
        "sol": sol, "solve_time": t_solve, "n": n, "nnz": nnz, "solver_name": solver
    }

def build_tridiag_sparse(n):
    dok = dok_matrix((n, n), dtype=np.float64)
    for i in range(n):
        dok[i, i] = 2.0
        if i > 0:
            dok[i, i-1] = -1.0
        if i < n-1:
            dok[i, i+1] = -1.0
    K = dok.tocsr()
    a_exact = np.ones(n)
    rhs = K @ a_exact
    return K, rhs, a_exact

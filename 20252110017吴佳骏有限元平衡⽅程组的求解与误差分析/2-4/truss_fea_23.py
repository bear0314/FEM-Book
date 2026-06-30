import numpy as np
import json

class TrussFEA23:
    def __init__(self, E, A):
        self.E = E
        self.A = A
        self.EA = E * A
        self.nodes = None
        self.elems = None
        self.n_dof = 0
        self.LM = None
        self.K_full = None
        self.F_full = None
        self.free_dof = []
        self.known_dof = []
        self.d_E = None
        self.K_FF = None
        self.K_EF = None
        self.rhs = None

    def set_model(self, nodes, elems):
        self.nodes = np.array(nodes, float)
        self.elems = np.array(elems, int)
        n_node = self.nodes.shape[0]
        self.n_dof = 2 * n_node
        self.LM = np.zeros((len(self.elems), 4), int)
        for e, (n1, n2) in enumerate(self.elems):
            self.LM[e] = [2*n1, 2*n1+1, 2*n2, 2*n2+1]
        self.K_full = np.zeros((self.n_dof, self.n_dof))
        self.F_full = np.zeros(self.n_dof)

    def elem_stiffness_2d(self, n1, n2):
        x1, y1 = self.nodes[n1]
        x2, y2 = self.nodes[n2]
        dx = x2 - x1
        dy = y2 - y1
        L = np.hypot(dx, dy)
        c = dx / L
        s = dy / L
        T = np.array([[c, s, 0, 0], [0, 0, c, s]])
        Kl = np.array([[1, -1], [-1, 1]]) * self.EA / L
        Ke = T.T @ Kl @ T
        return Ke

    def assemble_global(self):
        self.K_full.fill(0.0)
        for e in range(len(self.elems)):
            n1, n2 = self.elems[e]
            Ke = self.elem_stiffness_2d(n1, n2)
            lm = self.LM[e]
            for i in range(4):
                for j in range(4):
                    self.K_full[lm[i], lm[j]] += Ke[i, j]

    def apply_bc_load(self, disp_bc, nodal_load):
        self.F_full.fill(0.0)
        for dof, val in nodal_load.items():
            self.F_full[dof] = val
        self.known_dof = list(disp_bc.keys())
        self.d_E = np.array([disp_bc[d] for d in self.known_dof], float)
        self.free_dof = [i for i in range(self.n_dof) if i not in self.known_dof]
        KFF = self.K_full[np.ix_(self.free_dof, self.free_dof)]
        KEF = self.K_full[np.ix_(self.known_dof, self.free_dof)]
        fF = self.F_full[self.free_dof]
        rhs = fF - KEF.T @ self.d_E
        self.K_FF = KFF
        self.K_EF = KEF
        self.rhs = rhs

    def reconstruct_full_disp(self, d_F):
        d = np.zeros(self.n_dof)
        d[self.free_dof] = d_F
        d[self.known_dof] = self.d_E
        return d

    def calc_reaction(self, d_full):
        KEE = self.K_full[np.ix_(self.known_dof, self.known_dof)]
        d_F = d_full[self.free_dof]
        R_E = self.K_EF @ d_F + KEE @ self.d_E
        return dict(zip(self.known_dof, R_E))

    def calc_elem_force_stress(self, d_full):
        res = []
        for e, (n1, n2) in enumerate(self.elems):
            lm = self.LM[e]
            de = d_full[lm]
            x1, y1 = self.nodes[n1]
            x2, y2 = self.nodes[n2]
            dx = x2 - x1
            dy = y2 - y1
            L = np.hypot(dx, dy)
            c, s = dx/L, dy/L
            du = de[2] - de[0]
            dv = de[3] - de[1]
            strain = c*du + s*dv
            stress = self.E * strain
            force = stress * self.A
            res.append({"elem_idx":e, "force":force, "stress":stress})
        return res

    def export_json(self, path="truss_reduced.json"):
        out = {
            "Title": "2.3 truss reduced equation",
            "source_homework": "2-3 Global Stiffness Equations",
            "K_FF": self.K_FF.tolist(),
            "rhs": self.rhs.tolist(),
            "known_dof": self.known_dof,
            "free_dof": self.free_dof,
            "full_K": self.K_full.tolist(),
            "full_force": self.F_full.tolist(),
            "known_displacement": self.d_E.tolist()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        return out

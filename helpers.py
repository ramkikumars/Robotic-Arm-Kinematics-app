import sympy as sy
import pandas as pd
import math
import streamlit as st
from sympy.physics.units import degree
from st_aggrid import AgGrid, GridOptionsBuilder

th = lambda i: "\u03B8" + chr(0x2080 + i)  # theta-joint angle
al = lambda i: "\u03B1" + chr(0x2080 + i)  # alpha-link twist angle
d = lambda i: "d" + chr(0x2080 + i)  # d-joint offset
a = lambda i: "a" + chr(0x2080 + i)  # a-link length


def write_mat(mat, name=""):
    mat = sy.N(mat)
    mat = mat.xreplace({n: round(n, 4) for n in mat.atoms(sy.Number)})
    simp = lambda x: sy.trigsimp(x)
    mat.applyfunc(simp)
    lat = r"%s\small{%s}" % (name, sy.latex(mat))
    # return st.latex(sy.latex(mat))
    return st.latex(lat)


def create_ses_state(dict):
    for key, val in dict.items():
        if key not in st.session_state:
            st.session_state[key] = val


def display_table(df, update_mode, reload=False):
    df = df.astype(str)
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True)
    # gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb = gb.build()
    # st.write(gb)
    gb["columnDefs"][0]["pinned"] = "left"
    # st.write(gb)
    return AgGrid(
        df,
        gridOptions=gb,
        allow_unsafe_jscode=True,
        update_mode=update_mode,
        fit_columns_on_grid_load=True,
        height=250,
        theme='fresh',
        reload_data=reload,
    )


def delete_rows(df, rows_to_delete):
    df = df.astype(str)
    lookup = df.merge(rows_to_delete,
                      on=list(df.columns),
                      how='left',
                      indicator=True)
    _df = df.drop(lookup[lookup['_merge'] == 'both'].index)
    return _df


# def pretty_mat(mat):
#     mat = sy.N(mat)
#     mat = mat.xreplace({n: round(n, 4) for n in mat.atoms(sy.Number)})
#     simp = lambda x: sy.trigsimp(x)
#     mat.applyfunc(simp)
#     return mat  # .applyfunc(simp)


def create_parameteres_df(total_joints):
    data = [[i, d(i), th(i), a(i), al(i)] for i in range(1, total_joints + 1)]
    # joints = [f"Joint {i}" for i in range(1, total_joints + 1)]
    df = pd.DataFrame(
        data,
        columns=[
            "Joint", "Joint offset", "Joint angle", "Link length",
            "Link twist angle"
        ],
    )
    return df


def sub_mat(mat, sub_dict):
    for key, val in sub_dict.items():
        if key[0] == "\u03B8" or key == "\u03B1":
            sub_dict[key] = math.radians(val)
    mat = mat.subs(sub_dict)
    # mat = sy.N(mat)
    mat = mat.xreplace({n: round(n, 4) for n in mat.atoms(sy.Number)})
    # mat = mat.applyfunc(nsimp)
    return mat


class Transformations():

    def rot(self, axis, theta):
        I = sy.eye(3)
        for i in range(3):
            for j in range(3):
                if i != axis - 1 and j != axis - 1:
                    if i == j:
                        I[i, j] = sy.cos(theta)
                    elif i < j:
                        I[i, j] = ((-1)**axis) * sy.sin(theta)
                    else:
                        I[i, j] = -1 * I[j, i]
        return I

    def homog_rot(self, axis, theta):
        I = sy.eye(4)
        I[0:3, 0:3] = self.rot(axis, theta)
        return I

    def homog_trans(self, pt):
        I = sy.eye(4)
        I[0:3, 3] = sy.Matrix(pt)
        return I

    def screw(self, axis, theta, units):
        pt = [0, 0, 0]
        pt[axis - 1] = units
        screw_mat = self.homog_rot(axis, theta) * self.homog_trans(pt)
        return screw_mat

    def inv_homog(self, mat):
        rot_t = mat[0:3, 0:3].T
        p = mat[0:3, 3]
        mat1 = rot_t.row_join(-1 * rot_t * p)
        mat1 = mat1.col_join(mat[3, :])
        return mat1

    def mat_seq(self, df):
        mat = sy.eye(4)
        expr = "I"
        axis_dict = {'X': 1, 'Y': 2, 'Z': 3}
        col = df.columns
        mat_list = []
        for j in range(1, len(col)):
            sno = col[j][1]
            [frame, oprn, angle, about, x, y,
             z] = [df.iloc[i, j] for i in range(7)]
            if oprn == "Rotation":
                angle = math.radians(float(angle))
                temp_mat = self.homog_rot(axis_dict[about], angle)
            elif oprn == "Translation":
                temp_mat = self.homog_trans((float(x), float(y), float(z)))
            elif oprn == "Screw":
                angle = math.radians(float(angle))
                axis = axis_dict[about]
                unit = [x, y, z][axis - 1]
                temp_mat = self.screw(axis, angle, unit)
            if frame == "Global":
                expr = f"\\textcolor{{orange}}{{M_{{{sno}}}}}*" + expr
                mat = temp_mat * mat
            else:
                expr = expr + f"*\\textcolor{{Cyan}}{{M_{{{sno}}}}}"
                mat = mat * temp_mat
            mat_list.append((sno, frame, temp_mat))
        return expr, mat, mat_list


@st.cache(allow_output_mutation=True)
class ForwardKinematics(Transformations):

    def __init__(self, df):
        self.parameters_table, self.variables = self.format_table(df)
        self.all_trnsfm_mat = self.joint_trnsfm_mat()

    def format_table(self, df):
        variables = []
        for i in range(df.shape[0]):
            for j in range(1, df.shape[1]):
                try:
                    df.iloc[i, j] = float(df.iloc[i, j])
                    if j == 2 or j == 4:
                        df.iloc[i, j] = math.radians(df.iloc[i, j])
                        # df.iloc[i, j] = 1111
                except ValueError:
                    variables.append(df.iloc[i, j])
        return df, variables

    def joint_trnsfm_mat(self):
        trnsfm_mat = []
        df = self.parameters_table
        # Joint dis, Joint ang, link length, link twist angle
        for joint in range(df.shape[0]):
            [_, d, th, a, al] = df.iloc[joint].tolist()
            mat = self.screw(axis=3, theta=th, units=d) * \
                self.screw(axis=1, theta=al, units=a)
            trnsfm_mat.append(self.pretty_mat(mat))
        return trnsfm_mat

    @st.cache(allow_output_mutation=True)
    def link_transfm_mat(self, ref_joint, obs_joint):
        T = []
        T_expr = []
        flag = False
        ref, obs = ref_joint, obs_joint
        if ref_joint > obs_joint:
            (ref, obs) = (obs_joint, ref_joint)
            flag = True
        for i in range(ref, obs):
            mat = self.all_trnsfm_mat[i]
            T.append(mat)
            T_expr.append(f"T^{i+1}_{i}")
        link_mat = math.prod(T)
        l = len(T_expr)
        e1 = f"T^{obs_joint}_{ref_joint}"
        e2_ = "*".join(T_expr)
        e2 = ("&=" + e2_ + r"\\[10pt]") if l != 1 else ""
        e3, e4 = "", ""
        if flag:
            link_mat = self.inv_homog(link_mat)
            e = f"T^{obs}_{ref}"
            e3 = r"&=\left[%s\right]^{-1}" % (e)
            e4 = r"&=\left[%s\right]^{-1}\\[10pt]" % (
                e2_) if l != 1 else r"\\[10pt]"
            e2 = ""
        expr = e1 + e2 + e3 + e4
        return expr, self.pretty_mat(link_mat)

    def pretty_mat(self, mat):
        tsimp = lambda x: sy.trigsimp(x)
        nsimp = lambda x: sy.nsimplify(x)
        if mat.atoms(sy.Number):
            mat = sy.N(mat)
            mat = mat.xreplace({n: round(n, 4) for n in mat.atoms(sy.Number)})
            mat = mat.applyfunc(nsimp)
        mat = mat.applyfunc(tsimp)
        return mat  # .applyfunc(simp)

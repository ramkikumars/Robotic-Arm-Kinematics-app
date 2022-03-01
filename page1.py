import streamlit as st

import sympy as sy
import pandas as pd
from st_aggrid import GridUpdateMode
import helpers as func
from helpers import Transformations
from sympy.physics.units import degree


def app():
    st.subheader("Transformation calculator")
    ## Layout
    st.markdown("#### *Rotation:*")
    sec1 = st.columns((0.5, 1, 1))
    st.markdown("***")
    st.markdown("#### *Translation:*")
    sec2 = st.columns((0.5, 1, 1))
    st.markdown("***")
    st.markdown("#### *Screw:*")
    sec3 = st.columns((0.5, 1, 1))
    st.markdown("***")
    st.markdown("#### *Sequence:*")
    sec4 = st.columns((0.7, 0.5, 0.8, 0.5))
    sec5 = st.columns((1, 1, 1, 1, 1))
    st.markdown("***Sequence matrices:***")
    sec6 = st.columns(3)
    seq_table_col = ["Frame", "Operation", "Angle", "About", "X", "Y", "Z"]
    df = pd.DataFrame({'*': seq_table_col})
    state = st.session_state
    seq_states = {
        "seq_df": df,
        "seq_no": 0,
        "seq_mat": sy.eye(4),
        "seq_expr": "I",
    }
    func.create_ses_state(seq_states)
    mat = Transformations()
    with sec1[0]:
        axis_dict = {'X': 1, 'Y': 2, 'Z': 3}
        axis = st.selectbox("Choose the axis of rotation:", axis_dict.keys())
        angle = st.number_input('Angle(deg):', -180, 180, 0)
    with sec1[1]:
        st.markdown("***Formula:***")
        rot_mat = mat.homog_rot(axis_dict[axis], '\u03B8')
        func.write_mat(rot_mat)
    with sec1[2]:
        st.markdown("***Rotation matrix:***")
        sl = degree.scale_factor
        rot_mat = rot_mat.subs(
            {'\u03B8':
             angle * sl})  # scaling factor to convert degress to radians
        func.write_mat(rot_mat)
    with sec2[0]:
        x = st.number_input(label="x", value=0.0, step=1.0)
        y = st.number_input(label="y", value=0.0, step=1.0)
        z = st.number_input(label="z", value=0.0, step=1.0)
    with sec2[1]:
        st.markdown("***Formula:***")
        trans_ = mat.homog_trans(["x", "y", "z"])
        func.write_mat(trans_)
    with sec2[2]:
        # st.write("\n")
        # st.write("\n")
        trans_mat = mat.homog_trans((x, y, z))
        st.markdown("***Translation matrix:***")
        func.write_mat(trans_mat)
    with sec3[0]:
        scrw_axis = st.selectbox("Rotation along:", axis_dict.keys())
        scrw_angle = st.number_input('angle(deg):', -180, 180, 0)
        with st.empty():
            unit = st.number_input(
                label=f"Translation along  {scrw_axis} axis",
                value=0.0,
                step=1.0)
    with sec3[1]:
        st.markdown("***Formula:***")
        scrw_axis_ = axis_dict[scrw_axis]
        theta = '\u03B8'
        unit_ = scrw_axis.lower()
        screw_mat = mat.screw(scrw_axis_, theta, unit_)
        func.write_mat(screw_mat)
    with sec3[2]:
        st.markdown("***Screw matrix:***")
        sl = degree.scale_factor  # scaling factor to convert degress to radians
        screw_mat = screw_mat.subs({theta: scrw_angle, unit_: unit})
        func.write_mat(screw_mat)
    with sec4[0]:
        oprn_list = ["Translation", "Rotation", "Screw"]
        frame = st.radio("Choose the Frame:", ("Local", "Global"))
        oprn = st.selectbox("Choose operation:", oprn_list)
        # st.write(len(state.seq_df.columns))
        pt = ["-", "-", "-"]
        value = "-"
        about = "-"
        if oprn == "Translation":
            pt = [x, y, z]
        elif oprn == "Rotation":
            value, about = (angle, axis)
        elif oprn == "Screw":
            pt[scrw_axis_ - 1] = unit
            about = scrw_axis
            value = scrw_angle
        nxt_col = [
            frame,
            oprn,
            value,
            about,
        ] + pt

    with sec5[0]:
        if st.button("Add to sequence"):
            state.seq_df[f"M{state.seq_no + 1}"] = nxt_col
            state.seq_no = state.seq_no + 1
    with sec4[1]:
        df_ = pd.DataFrame({'*': seq_table_col})
        df_[f"M{state.seq_no + 1}"] = nxt_col
        st.markdown("***Current selection:***")
        st.dataframe(df_.astype(str))
    with sec4[0]:
        state.seq_no = 0 if len(state.seq_df.columns) == 1 else state.seq_no
        mat_no = state.seq_no + 1
        col = "Orange" if frame == "Global" else "Cyan"
        mat_name = r"\textcolor{%s}{M_%d}=" % (col,
                                               st.session_state.seq_no + 1)
        st.markdown("***Current matrix:***")
        with st.empty():
            idx = oprn_list.index(oprn)
            temp_mat = (rot_mat, trans_mat, screw_mat)[idx]
            func.write_mat(temp_mat, mat_name)
    with sec4[2]:
        st.markdown("***Summary:***")
        seq_table = func.display_table(
            state.seq_df, update_mode=GridUpdateMode.MODEL_CHANGED)
        seq_df_ = pd.DataFrame(seq_table["data"])
        state.seq_expr, state.seq_mat, mat_list = mat.mat_seq(seq_df_)
        i = 0
        for m in mat_list:
            n, f, mat = m
            col = "Orange" if f == "Global" else "Cyan"
            mat_name = r"\textcolor{%s}{M_%s}=" % (col, n)
            with sec6[i]:
                func.write_mat(mat, mat_name)
            i = i + 1
            i = 0 if i == 3 else i
    with sec4[3]:
        st.markdown("***Sequence formula:***")
        st.latex(r"\large{%s}" % state.seq_expr)
        # with sec4[3]:
        st.markdown("***Final Matrix:***")
        func.write_mat(state.seq_mat)
        st.markdown(r"""$\\[10pt]\textcolor{Cyan}{M_n}$ &rarr; Local frame
                        $\\[3pt]\textcolor{Orange}{M_n}$ &rarr; Global frame"""
                    )
    with sec5[1]:
        with st.expander("Delete").form("Delete"):
            col_name = state.seq_df.columns
            col_del = st.multiselect("Choose to delete:", col_name[1:])
            if st.form_submit_button("Delete"):
                state.seq_df = state.seq_df.drop(col_del, axis=1)
                st.experimental_rerun()
    with sec5[2]:
        if st.button("Reset"):
            for key in seq_states.keys():
                del st.session_state[key]
            st.experimental_rerun()
        st.caption("Resets the table, sequence expression and matrix")


# app()

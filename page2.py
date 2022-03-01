import streamlit as st
import pandas as pd
import sympy as sy
from st_aggrid import GridUpdateMode
import helpers as func


def app():
    st.subheader("Forward Kinematics Calculator")
    sec1 = st.columns((0.5, 1, 1))
    sec2 = st.columns((1, 1, 1, 4))
    sec3 = st.columns(1)
    state = st.session_state
    reload_data = False
    kin_states = {"mat_list": {}, "mat_no": 0, "allow": False}
    func.create_ses_state(kin_states)

    def flag():
        state.allow = False

    with sec1[0]:
        n = st.selectbox("No of Joints:", [*range(1, 10)], 4, on_change=flag)
        params_df = func.create_parameteres_df(n)
    with sec1[1]:
        st.markdown("***Parameters Table:***")
        dh_table = func.display_table(params_df,
                                      update_mode=GridUpdateMode.MANUAL,
                                      reload=reload_data)
    data_df = pd.DataFrame(dh_table["data"])
    frwd_kin = func.ForwardKinematics(data_df)
    variables = frwd_kin.variables
    i = 0
    variable_dict = {}
    with st.sidebar:
        st.markdown(">Variables in the parameters table")
        for var in variables:
            variable_dict[var] = st.number_input(var)
    with sec1[2]:
        st.markdown("***Arm Matrix:***")
        if st.button("Compute Arm Matrix") or state.allow:
            with st.spinner("Computing Arm Matrix"):
                expr, t_mat = frwd_kin.link_transfm_mat(0, n)
                t_mat_sub = sy.latex(func.sub_mat(t_mat, variable_dict))
                t_mat = sy.latex(t_mat)
                space = "\qquad" * 35
                eqn = r'''{\begin{align*}
                        %s&=%s\\[30pt]
                        &=%s%s
                        \end{align*}}''' % (expr, t_mat, t_mat_sub, space)
                st.latex(eqn)
                state.allow = True
    with sec1[0]:
        # st.markdown("***Link coordinate tranformation matrix:***")
        with st.form("form"):
            obs = st.selectbox("Source Coordinate frame", range(n + 1), 1)
            ref = st.selectbox("Reference Coordinate frame", range(n + 1))
            if st.form_submit_button("Add"):
                if len(state.mat_list) > 0:
                    state.mat_no += 1
                else:
                    state.mat_no = 1
                key = state.mat_no
                state.mat_list[key] = [ref, obs, ""]
    with sec2[0]:
        if st.button("Delete Selected"):
            rem_list = []
            for key, val in state.mat_list.items():
                if val[2] == True:
                    rem_list.append(key)
            l = [state.mat_list.pop(key) for key in rem_list]
    with sec2[1]:
        if st.button("Delete All"):
            rem_list = list(state.mat_list.keys())
            for key in rem_list:
                state.mat_list.pop(key)
    with sec3[0]:
        st.markdown("***Link Coordinate transformation matrix output:***")
        for key, val in state.mat_list.items():
            expr, t_mat = frwd_kin.link_transfm_mat(val[0], val[1])
            state.mat_list[key][2] = st.checkbox(f"{key}")
            t_mat_sub = sy.latex(func.sub_mat(t_mat, variable_dict))
            t_mat = sy.latex(t_mat)
            space = "\qquad" * 35
            eqn = r'''{\begin{align*}
                    %s&=%s\\[30pt]
                    &=%s%s
                    \end{align*}}\\\rule{25cm}{0.1mm}''' % (expr, t_mat,
                                                            t_mat_sub, space)
            st.latex(eqn)
            # if st.form_submit_button("k"):
            #     pass
    with sec2[2]:
        # st.write("\n")
        # st.write("\n")
        if st.button("Reset All"):
            for key in kin_states.keys():
                del st.session_state[key]
            reload_data = True
            st.experimental_rerun()


# app()

import streamlit as st
from multiapp import MultiApp
# from apps import home, data_stats # import your app modules here
import page1, page2

st.set_page_config(
    page_title="Kinematics App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)
hide_streamlit_style = \
        '''
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
    '''
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# CSS to inject contained in a string
hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

page = ['Tranformations', 'Forward Kinematics']
with st.sidebar:
    st.markdown("# *Robotic Arm Kinematics app*")
    st.markdown("""
        [![ramki](https://img.shields.io/badge/Author-@ramki-gray.svg?colorA=gray&colorB=dodgergreen&logo=github)](https://github.com/ramkikumars)
        """)
    if st.checkbox("Demo video"):
        st.video('https://youtu.be/4IqlUqK7bmc')
    if st.checkbox("Instructions"):
        st.markdown("""
                >For Transformations Calculator:
                1. If you want to add tranformation matrix to sequence, set the matrices in the respective sections (Rotation,Translation,Screw),choose the frame and operation, click ***Add to seq***
                2. ***Final Matrix*** is computed by multiplying the matrices in added seqeunce
                3. You can edit the table values, changes will be reflected in corresponding matrix and also in ***Final Matrix***
                >For Forward Kinematics Calculator:
                1. Enter your value in the ***parameters table*** and click update button
                2. Set the value of source frame and ref frame, click add button to compute the matrix
                3. Change the value of the variables below
                4. Observe the changes in the coordinate trsformation matrix and arm matrix
                5. You can add any number of tranformation matrix to the list, use ***Delete***, ***Delete All*** to remove from the list
                6. Use ***Reset*** to reset the table,list and arm matrix.
                    """)
    st.markdown("***")
    option = st.selectbox(
        'Select Page',
        page,
    )
if option == page[0]:
    page1.app()
elif option == page[1]:
    page2.app()
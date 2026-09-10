import streamlit as st
from utils.auth import render_login, _get_current_user, _get_current_member

# Login page: render inline — no st.switch_page (doesn't work with st.navigation).
if _get_current_user() is None and _get_current_member() is None:
    render_login()
else:
    st.info("You are already logged in. The page will refresh.")
    st.rerun()

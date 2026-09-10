import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, _get_current_user, _get_current_member, log_activity, SESSION_KEY, MEMBER_SESSION_KEY

st.set_page_config(page_title="SIAG", page_icon="🌌", layout="wide")

pages = [
    st.Page("pages/01_Dashboard.py", title="Dashboard", icon="🏠"),
    st.Page("pages/02_Members.py", title="Members", icon="👥"),
    st.Page("pages/03_Projects.py", title="Projects", icon="🏗️"),
    st.Page("pages/04_Media.py", title="Media", icon="🖼️"),
    st.Page("pages/05_Documents.py", title="Documents", icon="📄"),
    st.Page("pages/06_Activity_Log.py", title="Activity Log", icon="📋"),
    st.Page("pages/00_Login.py", title="Login", icon="🔑"),
]
nav = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.title("🌌 SIAG")
    st.caption("Societal Impact Action Group")

    # Logout: clears sessions, then reruns. The page guard detects empty session.
    user = _get_current_user()
    member = _get_current_member()
    if user is not None or member is not None:
        if st.button("Logout", key="btn_logout", type='secondary', width='stretch'):
            if user:
                log_activity(user.get('id'), 'logout', 'users', user.get('id'))
            if member:
                log_activity(None, 'logout', 'members', member.get('id'))
            st.session_state.pop(SESSION_KEY, None)
            st.session_state.pop(MEMBER_SESSION_KEY, None)
            st.rerun()

    st.divider()
    render_current_user_badge()
    render_current_member_badge()

nav.run()

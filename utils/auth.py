import os
import bcrypt
from dotenv import load_dotenv
from utils.db_utils import fetch_one, execute_write, log_activity

load_dotenv()

SESSION_KEY = 'siag_session_user'
MEMBER_SESSION_KEY = 'siag_session_member'


def _get_current_user():
    import streamlit as st
    return st.session_state.get(SESSION_KEY)


def _get_current_member():
    import streamlit as st
    return st.session_state.get(MEMBER_SESSION_KEY)


def require_login_or_member():
    import streamlit as st
    if _get_current_user() is None and _get_current_member() is None:
        _render_login_inline()
        st.stop()


def require_login():
    import streamlit as st
    if _get_current_user() is None and _get_current_member() is None:
        _render_login_inline()
        st.stop()


def require_member_login():
    import streamlit as st
    if _get_current_member() is None:
        _render_member_login_inline()
        st.stop()


def require_role(roles):
    """roles: iterable of allowed role strings, e.g. ('admin','editor').
    Members (member login) count as viewers — allowed if 'viewer' is in roles."""
    import streamlit as st
    user = _get_current_user()
    member = _get_current_member()
    if user is None and member is None:
        st.error("You do not have permission to access this page.")
        st.stop()
    if user is not None and user.get('role') not in roles:
        st.error("You do not have permission to access this page.")
        st.stop()
    if member is not None and 'viewer' not in roles:
        st.error("You do not have permission to access this page.")
        st.stop()


# ---- inline login (rendered on the calling page, no page switch) ----

def _render_login_inline():
    import streamlit as st
    st.title("SIAG Login")
    tab_user, tab_member = st.tabs(["Admin Login", "Member Login"])
    with tab_user:
        _render_user_form()
    with tab_member:
        _render_member_form()


def _render_member_login_inline():
    import streamlit as st
    st.title("Member Login")
    _render_member_form()


def _render_user_form():
    import streamlit as st
    with st.form('login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = fetch_one(
                "SELECT id, username, role, full_name, password_hash FROM users WHERE username = %s",
                (username,),
            )
            if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                st.session_state[SESSION_KEY] = {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'full_name': user['full_name'],
                }
                log_activity(user['id'], 'login', 'users', user['id'], f"User {username} logged in")
                st.success("Logged in.")
                st.rerun()
            else:
                st.error("Invalid username or password.")


def _render_member_form():
    import streamlit as st
    with st.form('member_login_form'):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            member = fetch_one(
                "SELECT id, first_name, last_name, email, password_hash FROM members WHERE email = %s",
                (email,),
            )
            if member and member.get('password_hash') and bcrypt.checkpw(password.encode(), member['password_hash'].encode()):
                st.session_state[MEMBER_SESSION_KEY] = {
                    'id': member['id'],
                    'first_name': member['first_name'],
                    'last_name': member['last_name'],
                    'email': member['email'],
                }
                log_activity(None, 'login', 'members', member['id'], f"Member {email} logged in")
                st.success("Logged in as member.")
                st.rerun()
            else:
                st.error("Invalid member email or password.")


# ---- page-level renderers (for pages/00_Login.py) ----

def render_login():
    """Full login page render."""
    import streamlit as st
    if _get_current_user() is not None or _get_current_member() is not None:
        st.info("Already logged in.")
        st.rerun()
        return
    _render_login_inline()


def render_member_login():
    """Member-only login form."""
    import streamlit as st
    _render_member_form()


# ---- logout / badges ----

def render_logout():
    import streamlit as st
    user = _get_current_user()
    member = _get_current_member()
    if user is None and member is None:
        return
    clicked = st.button("Logout", key="btn_logout", type='secondary', width='stretch')
    if clicked:
        if user:
            log_activity(user.get('id'), 'logout', 'users', user.get('id'))
        if member:
            log_activity(None, 'logout', 'members', member.get('id'))
        st.session_state.pop(SESSION_KEY, None)
        st.session_state.pop(MEMBER_SESSION_KEY, None)
        st.rerun()


def render_current_user_badge():
    import streamlit as st
    user = _get_current_user()
    if user:
        st.caption(f"Signed in as **{user.get('full_name') or user.get('username')}** - role: `{user['role']}`")


def render_current_member_badge():
    import streamlit as st
    member = _get_current_member()
    if member:
        st.caption(f"Signed in as **{member.get('first_name')} {member.get('last_name')}** - member")

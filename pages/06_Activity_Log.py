import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role, _get_current_user
from utils.db_utils import fetch_all, execute_write, log_activity

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("Activity Log")

# Flash message (persists across reruns)
if st.session_state.get('flash_msg'):
    fmsg = st.session_state['flash_msg']
    if st.session_state.get('flash_type') == 'error':
        st.error(fmsg)
    else:
        st.success(fmsg)
    del st.session_state['flash_msg']
    del st.session_state['flash_type']

render_current_user_badge()
render_current_member_badge()

# Purge button — admin only
user = _get_current_user()
if user and user.get('role') == 'admin':
    st.divider()
    st.subheader("Admin: Purge Activity Log")
    st.caption("This will permanently delete all activity log entries. This action cannot be undone.")
    if st.button("Purge Activity Log", type='primary', width='stretch'):
        st.session_state['pending_delete'] = {
            'type': 'purge',
            'id': None,
            'label': 'All activity log entries',
        }
        st.rerun()

st.divider()
rows = fetch_all(
    "SELECT al.*, u.username, u.full_name FROM activity_log al "
    "LEFT JOIN users u ON al.user_id = u.id "
    "ORDER BY al.created_at DESC LIMIT 500"
)
if rows:
    st.dataframe(rows, width='stretch')
else:
    st.info("No activity recorded yet.")

# --- Delete confirmation ---
pending = st.session_state.get('pending_delete')
if pending and pending.get('type') == 'purge':
    st.warning(f"⚠️ Are you sure you want to delete **{pending['label']}**? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, purge", type="primary", key="confirm_purge", use_container_width=True):
        execute_write("DELETE FROM activity_log")
        log_activity(user['id'], 'purge', 'activity_log', None, "Purged all activity log entries")
        st.session_state['pending_delete'] = None
        st.query_params["flash"] = "Purged all activity log entries."
        st.query_params["flash_type"] = "success"
        st.rerun()
    if c2.button("Cancel", key="cancel_purge", use_container_width=True):
        st.session_state['pending_delete'] = None
        st.rerun()

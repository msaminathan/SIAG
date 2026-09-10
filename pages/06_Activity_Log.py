import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role, _get_current_user
from utils.db_utils import fetch_all, execute_write, log_activity

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("Activity Log")

render_current_user_badge()
render_current_member_badge()

# Purge button — admin only
user = _get_current_user()
if user and user.get('role') == 'admin':
    st.divider()
    st.subheader("Admin: Purge Activity Log")
    st.caption("This will permanently delete all activity log entries. This action cannot be undone.")
    if st.button("Purge Activity Log", type='primary', width='stretch'):
        count = execute_write("DELETE FROM activity_log")
        log_activity(user['id'], 'purge', 'activity_log', None, f"Purged all activity log entries")
        st.success(f"Purged all activity log entries.")
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

import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role
from utils.db_utils import fetch_all

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("SIAG Dashboard")

render_current_user_badge()
render_current_member_badge()

st.divider()

# KPI cards
member_count = fetch_all("SELECT COUNT(*) AS c FROM members")[0]['c']
active_projects = fetch_all("SELECT COUNT(*) AS c FROM projects WHERE status='Active'")[0]['c']
media_count = fetch_all("SELECT COUNT(*) AS c FROM media")[0]['c']
doc_count = fetch_all("SELECT COUNT(*) AS c FROM documents")[0]['c']

col1, col2, col3, col4 = st.columns(4)
col1.metric("Members", member_count)
col2.metric("Active Projects", active_projects)
col3.metric("Media Items", media_count)
col4.metric("Documents", doc_count)

st.divider()

st.subheader("Recent Activity")
rows = fetch_all(
    "SELECT al.created_at, u.username, al.action, al.entity_type, al.details "
    "FROM activity_log al "
    "LEFT JOIN users u ON al.user_id = u.id "
    "ORDER BY al.created_at DESC LIMIT 20"
)
if rows:
    for r in rows:
        st.write(f"**{r['created_at']}** `{r['username']}` - {r['action']} on {r['entity_type']}: {r['details']}")
else:
    st.info("No activity yet.")

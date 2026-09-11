import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role, _get_current_user
from utils.db_utils import fetch_all, fetch_one, execute_write, log_activity
from utils.uploads import save_upload, delete_file

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("Projects")

render_current_user_badge()
render_current_member_badge()

search = st.text_input("Search projects by name / village / district").strip().lower()
base_query = """
    SELECT p.*, 
           (SELECT COUNT(*) FROM project_updates pu WHERE pu.project_id = p.id) AS update_count
    FROM projects p
"""
params = None
if search:
    base_query += " WHERE LOWER(p.project_name) LIKE %s OR LOWER(p.village) LIKE %s OR LOWER(p.district) LIKE %s"
    like = f"%{search}%"
    params = (like, like, like)
base_query += " ORDER BY p.created_at DESC"

rows = fetch_all(base_query, params)

for r in rows:
    with st.expander(f"{'★ ' if r.get('is_featured') else ''}{r['project_name']} - {r.get('status')}"):
        col1, col2, col3 = st.columns(3)
        col1.write(f"**Category:** {r.get('category') or '-'}")
        col1.write(f"**Village:** {r.get('village') or '-'}")
        col2.write(f"**District:** {r.get('district') or '-'}")
        col2.write(f"**State:** {r.get('state') or '-'}")
        col3.write(f"**Lead:** {r.get('project_lead') or '-'}")
        col3.write(f"**Status:** {r.get('status') or '-'}")
        st.write(f"**Description:** {r.get('description') or '-'}")
        st.write(f"**Outcome Summary:** {r.get('outcome_summary') or '-'}")
        st.caption(f"Updates: {r.get('update_count', 0)} | Start: {r.get('start_date')} | End: {r.get('end_date')}")

        if _get_current_user() and _get_current_user().get('role') in ('admin', 'editor') and st.button("Delete", key=f"del_proj_{r['id']}", type='secondary'):
            execute_write("DELETE FROM projects WHERE id = %s", (r['id'],))
            log_activity(_get_current_user()['id'], 'delete', 'projects', r['id'])
            st.success("Project deleted.")
            st.rerun()

        if _get_current_user() and _get_current_user().get('role') in ('admin', 'editor') and st.button("Edit", key=f"edit_proj_{r['id']}", type='primary'):
            st.session_state['editing_project_id'] = r['id']
            st.rerun()

# --- Add / Edit Project (admin / editor) ---
user_role = _get_current_user().get('role') if _get_current_user() else None
if user_role in ('admin', 'editor'):
    st.divider()
    editing_id = st.session_state.get('editing_project_id')
    if editing_id:
        existing = fetch_one("SELECT * FROM projects WHERE id = %s", (editing_id,))
        if existing:
            st.subheader(f"Update Project: {existing['project_name']}")
        else:
            st.session_state['editing_project_id'] = None
            st.rerun()
    else:
        st.subheader("Add New Project")
    with st.form("add_project"):
        if editing_id and existing:
            name = st.text_input("Project Name*", value=existing.get('project_name') or "")
            desc = st.text_area("Description", value=existing.get('description') or "")
            col1, col2 = st.columns(2)
            cat = col1.text_input("Category", value=existing.get('category') or "")
            village = col2.text_input("Village", value=existing.get('village') or "")
            col_a, col_b, col_c = st.columns(3)
            district = col_a.text_input("District", value=existing.get('district') or "")
            state = col_b.text_input("State", value=existing.get('state') or "")
            status = col_c.selectbox("Status", ["Planning", "Active", "On Hold", "Completed", "Closed"], index=["Planning", "Active", "On Hold", "Completed", "Closed"].index(existing.get('status') or "Planning") if (existing.get('status') or "Planning") in ["Planning", "Active", "On Hold", "Completed", "Closed"] else 0)
            col_d, col_e = st.columns(2)
            start = col_d.date_input("Start Date", value=existing.get('start_date') if existing.get('start_date') else None)
            end = col_e.date_input("End Date", value=existing.get('end_date') if existing.get('end_date') else None)
            lead = st.text_input("Project Lead", value=existing.get('project_lead') or "")
            budget = st.number_input("Budget (INR)", min_value=0.0, step=1000.0, value=float(existing.get('budget_in_inr') or 0.0))
            outcome = st.text_area("Outcome Summary", value=existing.get('outcome_summary') or "")
        else:
            name = st.text_input("Project Name*")
            desc = st.text_area("Description")
            col1, col2 = st.columns(2)
            cat = col1.text_input("Category")
            village = col2.text_input("Village")
            col_a, col_b, col_c = st.columns(3)
            district = col_a.text_input("District")
            state = col_b.text_input("State")
            status = col_c.selectbox("Status", ["Planning", "Active", "On Hold", "Completed", "Closed"])
            col_d, col_e = st.columns(2)
            start = col_d.date_input("Start Date")
            end = col_e.date_input("End Date")
            lead = st.text_input("Project Lead")
            budget = st.number_input("Budget (INR)", min_value=0.0, step=1000.0)
            outcome = st.text_area("Outcome Summary")
        submitted = st.form_submit_button("Update Project" if editing_id else "Save Project")
        if submitted and name:
            if editing_id and existing:
                execute_write(
                    "UPDATE projects SET project_name=%s,description=%s,category=%s,village=%s,"
                    "district=%s,state=%s,status=%s,start_date=%s,end_date=%s,"
                    "project_lead=%s,budget_in_inr=%s,outcome_summary=%s,updated_by=%s WHERE id=%s",
                    (name,desc or None,cat or None,village or None,district or None,state or None,
                     status,start,end,lead or None,budget,outcome or None,
                     _get_current_user()['id'],editing_id))
                log_activity(_get_current_user()['id'],'update','projects',editing_id,details=f"Updated {name}")
                st.success(f"Project updated: {name}")
                st.session_state['editing_project_id'] = None
                st.rerun()
            else:
                execute_write(
                    "INSERT INTO projects (project_name,description,category,village,district,state,status,start_date,end_date,"
                    "budget_in_inr,project_lead,outcome_summary,created_by,updated_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (name, desc or None, cat or None, village or None, district or None, state or None, status, start, end, lead or None, budget, outcome or None,
                 _get_current_user()['id'],
                 _get_current_user()['id']),
            )
            log_activity(_get_current_user()['id'], 'create', 'projects', details=name)
            st.success("Project added.")
            st.rerun()

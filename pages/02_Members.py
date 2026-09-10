import streamlit as st
import bcrypt
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, _get_current_user, _get_current_member
from utils.db_utils import fetch_all, fetch_one, execute_write, log_activity
from utils.uploads import save_upload, delete_file

require_login_or_member()
is_admin_or_editor = _get_current_user() is not None and _get_current_user().get('role') in ('admin','editor')

st.title("Members")

if st.query_params.get("status") == "password_updated":
    mn = st.query_params.get("member","Member")
    st.success(f"Password updated for **{mn}**")
    st.query_params.clear()

render_current_user_badge()
render_current_member_badge()

search = st.text_input("Search members by name / email").strip().lower()
bq = "SELECT * FROM members"
params = None
if search:
    bq += " WHERE LOWER(first_name) LIKE %s OR LOWER(last_name) LIKE %s OR LOWER(email) LIKE %s"
    like = f"%{search}%"
    params = (like, like, like)
bq += " ORDER BY created_at DESC"
rows = fetch_all(bq, params)

if rows:
    for r in rows:
        with st.expander(f"{r['first_name']} {r['last_name']} - {r.get('role_in_siag') or 'Member'}"):
            cols = st.columns([1,1,1])
            cols[0].write(f"**Email:** {r.get('email') or '-'}")
            cols[1].write(f"**Phone:** {r.get('phone') or '-'}")
            cols[2].write(f"**Active:** {'Yes' if r.get('is_active') else 'No'}")
            st.write(f"**Graduation Year:** {r.get('graduation_year') or '-'}")
            st.write(f"**Department:** {r.get('department') or '-'}")
            st.write(f"**Notes:** {r.get('notes') or '-'}")
            if is_admin_or_editor:
                ce, cd = st.columns([1,4])
                if ce.button("Edit", key=f"edit_mem_{r['id']}", width='stretch'):
                    st.session_state['editing_member_id'] = r['id']
                    st.rerun()
                if cd.button("Delete", key=f"del_{r['id']}", type='secondary', width='stretch'):
                    execute_write("DELETE FROM members WHERE id = %s", (r['id'],))
                    log_activity(_get_current_user()['id'], 'delete', 'members', r['id'])
                    st.success("Deleted.")
                    st.rerun()
else:
    st.info("No members found.")

user_role = _get_current_user().get('role') if _get_current_user() else None
if user_role in ('admin','editor'):
    st.divider()
    eid = st.session_state.get('editing_member_id')
    member = None
    if eid:
        member = fetch_one("SELECT * FROM members WHERE id = %s", (eid,))
        if member:
            st.subheader(f"Update Member: {member['first_name']} {member['last_name']}")
        else:
            st.session_state['editing_member_id'] = None
            st.rerun()
    else:
        st.subheader("Add New Member")

    with st.form("add_member"):
        c1, c2 = st.columns(2)
        if eid and member:
            fn = c1.text_input("First Name*", value=member['first_name'], key="efn")
            ln = c2.text_input("Last Name*", value=member['last_name'], key="eln")
            email = st.text_input("Email", value=member.get('email') or '', key="eem")
            phone = st.text_input("Phone", value=member.get('phone') or '', key="eph")
            ca, cb, cc = st.columns(3)
            grad = ca.number_input("Graduation Year", min_value=0, max_value=2099, step=1, value=member.get('graduation_year') or 0, key="egr")
            dept = cb.text_input("Department", value=member.get('department') or '', key="edpt")
            role_in = cc.text_input("Role in SIAG", value=member.get('role_in_siag') or '', key="erol")
            notes = st.text_area("Notes", value=member.get('notes') or '', key="enote")
            member_password = st.text_input("Password (leave blank to keep current)", type="password", key="epw")
        else:
            fn = c1.text_input("First Name*")
            ln = c2.text_input("Last Name*")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            ca, cb, cc = st.columns(3)
            grad = ca.number_input("Graduation Year", min_value=0, max_value=2099, step=1)
            dept = cb.text_input("Department")
            role_in = cc.text_input("Role in SIAG")
            notes = st.text_area("Notes")
            member_password = st.text_input("Password (optional)", type="password")
        submitted = st.form_submit_button("Update Member" if eid else "Save Member")
        if submitted and fn and ln:
            pw = None
            if member_password:
                pw = bcrypt.hashpw(member_password.encode(), bcrypt.gensalt()).decode()
            if eid and member:
                if pw:
                    execute_write(
                        "UPDATE members SET first_name=%s,last_name=%s,email=%s,phone=%s,"
                        "graduation_year=%s,department=%s,role_in_siag=%s,password_hash=%s,"
                        "notes=%s,updated_by=%s WHERE id=%s",
                        (fn,ln,email or None,phone or None,grad or None,dept or None,
                         role_in or None,pw,notes or None,_get_current_user()['id'],eid))
                else:
                    execute_write(
                        "UPDATE members SET first_name=%s,last_name=%s,email=%s,phone=%s,"
                        "graduation_year=%s,department=%s,role_in_siag=%s,"
                        "notes=%s,updated_by=%s WHERE id=%s",
                        (fn,ln,email or None,phone or None,grad or None,dept or None,
                         role_in or None,notes or None,_get_current_user()['id'],eid))
                log_activity(_get_current_user()['id'],'update','members',eid,details=f"Updated {fn} {ln}")
                st.success(f"Member updated: {fn} {ln}")
                st.session_state['editing_member_id'] = None
                st.rerun()
            else:
                execute_write(
                    "INSERT INTO members (first_name,last_name,email,phone,graduation_year,department,role_in_siag,password_hash,notes,created_by,updated_by) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (fn,ln,email or None,phone or None,grad or None,dept or None,
                     role_in or None,pw,notes or None,_get_current_user()['id'],_get_current_user()['id']))
                log_activity(_get_current_user()['id'],'create','members',details=f"{fn} {ln}")
                st.success("Member added.")
                st.rerun()

    st.divider()
    st.subheader("Set Member Password")
    with st.form("set_member_password"):
        opts = {f"{r['id']}: {r['first_name']} {r['last_name']} ({r.get('email') or '-'})": r['id'] for r in fetch_all("SELECT id,first_name,last_name,email FROM members ORDER BY created_at DESC")}
        sel = st.selectbox("Select Member", list(opts.keys()))
        new_pw = st.text_input("New Password", type="password")
        sp = st.form_submit_button("Update Password")
        if sp and new_pw and sel in opts:
            mid = opts[sel]
            execute_write("UPDATE members SET password_hash=%s WHERE id=%s",
                          (bcrypt.hashpw(new_pw.encode(),bcrypt.gensalt()).decode(),mid))
            log_activity(_get_current_user()['id'],'update','members',mid,details='Updated member password')
            st.query_params.update(status="password_updated",member=sel.split(':')[0].strip())
            st.rerun()

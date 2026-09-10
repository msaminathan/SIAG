import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role, _get_current_user
from utils.db_utils import fetch_all, fetch_one, execute_write, log_activity
from utils.uploads import save_upload, delete_file

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("Documents")

render_current_user_badge()
render_current_member_badge()

# Initialize edit state
if 'editing_doc_id' not in st.session_state:
    st.session_state['editing_doc_id'] = None

# Edit state: reset on rerun after update
if st.session_state.get('editing_doc_id') is None and st.session_state.get('_clear_edit'):
    st.session_state['_clear_edit'] = False
    st.session_state['editing_doc_id'] = None

# Upload section (admin / editor)
user_role = _get_current_user().get('role') if _get_current_user() else None
if user_role in ('admin', 'editor'):
    st.divider()
    st.subheader("Upload Document")
    with st.form("upload_doc"):
        title = st.text_input("Title*")
        description = st.text_area("Description")
        tags = st.text_input("Tags (comma separated)")
        related_type = st.selectbox("Related to", ["general", "project", "member"])
        related_id = st.number_input("Related ID (optional)", min_value=0, value=0)
        file = st.file_uploader("Upload File", type=["pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"])
        submitted = st.form_submit_button("Upload")
        if submitted and title and file:
            stored = save_upload(file, subfolder='documents')
            size_kb = round(len(file.getvalue()) / 1024)
            execute_write(
                "INSERT INTO documents (title, description, file_path, file_type, file_size_kb, related_type, related_id, uploaded_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (title, description or None, stored, file.type or None, size_kb,
                 related_type if related_type != 'general' else 'general',
                 related_id if related_id else None,
                 _get_current_user()['id']),
            )
            log_activity(_get_current_user()['id'], 'create', 'documents', details=title)
            st.success("Document uploaded.")
            st.rerun()

# Edit Document form (admin / editor)
if user_role in ('admin', 'editor') and st.session_state.get('editing_doc_id') is not None:
    edit_id = st.session_state['editing_doc_id']
    edit_doc = fetch_one("SELECT * FROM documents WHERE id = %s", (edit_id,))
    if edit_doc is None:
        st.session_state['editing_doc_id'] = None
        st.rerun()
    st.divider()
    st.subheader("Update Document")
    with st.form("edit_doc"):
        edit_title = st.text_input("Title*", value=edit_doc['title'])
        edit_description = st.text_area("Description", value=edit_doc.get('description') or '')
        edit_tags = st.text_input("Tags (comma separated)", value=edit_doc.get('tags') or '')
        edit_related_type = st.selectbox("Related to", ["general", "project", "member"],
                                         index=["general", "project", "member"].index(edit_doc.get('related_type') or 'general'))
        edit_related_id = st.number_input("Related ID (optional)", min_value=0, value=edit_doc.get('related_id') or 0)
        edit_file = st.file_uploader("Replace file (optional)", type=["pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"])
        edit_submitted = st.form_submit_button("Update Document")
        if edit_submitted and edit_title:
            new_path = edit_doc['file_path']
            new_type = edit_doc.get('file_type')
            new_size_kb = edit_doc.get('file_size_kb', 0)
            if edit_file is not None:
                new_path = save_upload(edit_file, subfolder='documents')
                new_type = edit_file.type or None
                new_size_kb = round(len(edit_file.getvalue()) / 1024)
                delete_file(edit_doc['file_path'])
            execute_write(
                "UPDATE documents SET title=%s, description=%s, tags=%s, file_path=%s, file_type=%s, file_size_kb=%s, related_type=%s, related_id=%s WHERE id=%s",
                (edit_title, edit_description or None, edit_tags or None,
                 new_path, new_type, new_size_kb,
                 edit_related_type if edit_related_type != 'general' else 'general',
                 edit_related_id if edit_related_id else None, edit_id),
            )
            log_activity(_get_current_user()['id'], 'update', 'documents', details=edit_title)
            st.session_state['_clear_edit'] = True
            st.session_state['editing_doc_id'] = None
            st.success(f"Updated: {edit_title}")
            st.rerun()

st.divider()

rows = fetch_all("SELECT * FROM documents ORDER BY created_at DESC")
if not rows:
    st.info("No documents yet.")
else:
    for r in rows:
        with st.expander(f"{r['title']} ({r.get('file_type') or '?'} - {r.get('file_size_kb', 0)} KB"):
            st.write(f"**Description:** {r.get('description') or '-'}")
            st.write(f"**Version:** {r.get('version') or '1.0'}")
            st.write(f"**Related:** {r.get('related_type')} {r.get('related_id') or ''}")
            # Read file once for both download and inline preview
            try:
                with open(r['file_path'], 'rb') as fh:
                    file_data = fh.read()
            except FileNotFoundError:
                st.warning("File not found on disk.")
                file_data = None

            if file_data is not None:
                # Download button (works for all file types)
                st.download_button(
                    label="Download file",
                    data=file_data,
                    file_name=r['title'] + ('.pdf' if r.get('file_type') == 'pdf' else ''),
                    mime=r.get('file_type') or 'application/octet-stream',
                    key=f"dl_doc_{r['id']}",
                )
                # Inline PDF viewer
                if r.get('file_type') == 'pdf':
                    try:
                        import base64
                        b64 = base64.b64encode(file_data).decode()
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{b64}" '
                            f'width="100%" height="600" type="application/pdf"></iframe>',
                            unsafe_allow_html=True,
                        )
                    except Exception:
                        pass
            if user_role in ('admin', 'editor'):
                col1, col2 = st.columns([1, 4])
                if col1.button("Edit", key=f"edit_doc_{r['id']}", width='stretch'):
                    st.session_state['editing_doc_id'] = r['id']
                    st.rerun()
                if col2.button("Delete", key=f"del_doc_{r['id']}", type='secondary', width='stretch'):
                    delete_file(r['file_path'])
                    execute_write("DELETE FROM documents WHERE id = %s", (r['id'],))
                    log_activity(_get_current_user()['id'], 'delete', 'documents', r['id'])
                    st.success("Deleted.")
                    st.rerun()

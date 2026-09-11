import streamlit as st
from utils.auth import render_current_user_badge, render_current_member_badge, require_login_or_member, require_role, _get_current_user
from utils.db_utils import fetch_all, fetch_one, execute_write, log_activity
from utils.uploads import save_upload, delete_file

require_login_or_member()
require_role(('admin', 'editor', 'viewer'))

st.title("Media Gallery")

render_current_user_badge()
render_current_member_badge()

# Fetch videos and photos separately — videos always render first
videos = fetch_all("SELECT * FROM media WHERE media_type = 'video' ORDER BY created_at DESC")
photos = fetch_all("SELECT * FROM media WHERE media_type = 'photo' ORDER BY created_at DESC")

user_role = _get_current_user().get('role') if _get_current_user() else None

# --- Existing videos on top ---
if videos:
    st.divider()
    st.subheader("Videos")
    for r in videos:
        with st.expander(f"[VIDEO] {r['title']}"):
            st.video(r['file_path'])
            st.write(f"**Tags:** {r.get('tags') or '-'}")
            st.write(f"**Related:** {r.get('related_type')} {r.get('related_id') or ''}")
            if user_role in ('admin', 'editor'):
                if st.button("Delete", key=f"del_media_{r['id']}", type='secondary'):
                    delete_file(r['file_path'])
                    execute_write("DELETE FROM media WHERE id = %s", (r['id'],))
                    log_activity(_get_current_user()['id'], 'delete', 'media', r['id'])
                    st.success("Deleted.")
                    st.rerun()
                if st.button("Edit", key=f"edit_media_{r['id']}", type='primary'):
                    st.session_state['editing_media_id'] = r['id']
                    st.rerun()

# --- Upload section (admin / editor) ---
if user_role in ('admin', 'editor'):
    st.divider()
    st.subheader("Upload Media")
    with st.form("upload_media"):
        title = st.text_input("Title*")
        media_type = st.selectbox("Type", ["photo", "video"])
        caption = st.text_area("Caption")
        tags = st.text_input("Tags (comma separated)")
        related_type = st.selectbox("Related to", ["general", "project", "member"])
        related_id = st.number_input("Related ID (optional)", min_value=0, value=0)
        file = st.file_uploader("Upload File", type=["jpg", "jpeg", "png", "gif", "mp4", "mov"])
        submitted = st.form_submit_button("Upload")
        if submitted and title and file:
            stored = save_upload(file, subfolder='media')
            execute_write(
                "INSERT INTO media (title, media_type, file_path, caption, tags, related_type, related_id, uploaded_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (title, media_type, stored, caption or None, tags or None,
                 related_type if related_type != 'general' else 'general',
                 related_id if related_id else None,
                 _get_current_user()['id']),
            )
            log_activity(_get_current_user()['id'], 'create', 'media', details=title)
            st.success("Media uploaded.")
            st.rerun()

# --- Edit Media form (admin / editor) ---
if user_role in ('admin', 'editor') and st.session_state.get('editing_media_id'):
    edit_id = st.session_state['editing_media_id']
    edit_item = fetch_one("SELECT * FROM media WHERE id = %s", (edit_id,))
    if not edit_item:
        st.warning("Media item not found.")
        st.session_state['editing_media_id'] = None
        st.rerun()
    st.divider()
    st.subheader("Update Media")
    with st.form("edit_media"):
        edit_title = st.text_input("Title*", value=edit_item['title'])
        edit_media_type = st.selectbox("Type", ["photo", "video"], index=0 if edit_item['media_type'] == 'photo' else 1)
        edit_caption = st.text_area("Caption", value=edit_item.get('caption') or "")
        edit_tags = st.text_input("Tags (comma separated)", value=edit_item.get('tags') or "")
        edit_related_type = st.selectbox(
            "Related to", ["general", "project", "member"],
            index=(["general", "project", "member"].index(edit_item['related_type'])
                   if edit_item['related_type'] in ("general", "project", "member")
                   else 0)
        )
        edit_related_id = st.number_input("Related ID (optional)", min_value=0, value=edit_item['related_id'] or 0)
        edit_file = st.file_uploader("Upload New File (optional)", type=["jpg", "jpeg", "png", "gif", "mp4", "mov"])
        edit_submitted = st.form_submit_button("Update Media")
        if edit_submitted and edit_title:
            new_path = None
            if edit_file:
                new_path = save_upload(edit_file, subfolder='media')
                if edit_item['file_path']:
                    delete_file(edit_item['file_path'])
            else:
                new_path = edit_item['file_path']
            execute_write(
                "UPDATE media SET title=%s, media_type=%s, file_path=%s, caption=%s, tags=%s, related_type=%s, related_id=%s WHERE id=%s",
                (edit_title, edit_media_type, new_path, edit_caption or None, edit_tags or None,
                 edit_related_type if edit_related_type != 'general' else 'general',
                 edit_related_id if edit_related_id else None,
                 edit_id),
            )
            log_activity(_get_current_user()['id'], 'update', 'media', edit_id, details=edit_title)
            st.success(f"Updated: {edit_title}")
            st.session_state['editing_media_id'] = None
            st.rerun()

# --- Existing photos ---
if photos:
    st.divider()
    st.subheader("Photos")
    for r in photos:
        with st.expander(f"[PHOTO] {r['title']}"):
            st.image(r['file_path'], caption=r.get('caption'), use_column_width=True)
            st.write(f"**Tags:** {r.get('tags') or '-'}")
            st.write(f"**Related:** {r.get('related_type')} {r.get('related_id') or ''}")
            if user_role in ('admin', 'editor'):
                if st.button("Delete", key=f"del_media_{r['id']}", type='secondary'):
                    delete_file(r['file_path'])
                    execute_write("DELETE FROM media WHERE id = %s", (r['id'],))
                    log_activity(_get_current_user()['id'], 'delete', 'media', r['id'])
                    st.success("Deleted.")
                    st.rerun()
                if st.button("Edit", key=f"edit_media_{r['id']}", type='primary'):
                    st.session_state['editing_media_id'] = r['id']
                    st.rerun()

# Empty state
if not videos and not photos:
    st.info("No media items yet.")

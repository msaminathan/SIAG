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


def is_url(path):
    """Check if file_path is a remote URL vs a local file path."""
    return path and (path.startswith('http://') or path.startswith('https://'))


def is_youtube_url(url):
    """Check if a URL points to a YouTube video."""
    if not url:
        return False
    return 'youtube.com' in url or 'youtu.be' in url


# --- Existing videos on top ---
if videos:
    st.divider()
    st.subheader("Videos")
    for r in videos:
        with st.expander(f"[VIDEO] {r['title']}"):
            fp = r['file_path']
            if is_url(fp):
                if is_youtube_url(fp):
                    st.video(fp)
                else:
                    st.warning("Non-YouTube video link — direct playback may not be supported.")
                    st.link_button("Open Video", fp)
            else:
                st.video(fp)
            st.write(f"**Tags:** {r.get('tags') or '-'}")
            st.write(f"**Related:** {r.get('related_type')} {r.get('related_id') or ''}")
            st.write(f"**Source:** {'Link' if is_url(fp) else 'Uploaded File'}")
            if user_role in ('admin', 'editor'):
                if st.button("Delete", key=f"del_media_{r['id']}", type='secondary'):
                    if not is_url(fp):
                        delete_file(fp)
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
    media_type = st.selectbox(
        "Type",
        ["photo", "video"],
        key="upload_media_type",
    )
    with st.form("upload_media"):

        title = st.text_input("Title*")

        # Source options depend on media type
        if media_type == "photo":
            source_options = ["Upload File", "Photo Link"]
        else:
            source_options = ["Upload File", "YouTube Video", "Video Link"]
        source_type = st.radio(
            "Source",
            source_options,
            horizontal=True,
            label_visibility="collapsed",
        )

        caption = st.text_area("Caption")
        tags = st.text_input("Tags (comma separated)")
        related_type = st.selectbox("Related to", ["general", "project", "member"])
        related_id = st.number_input("Related ID (optional)", min_value=0, value=0)

        file_path = None
        if source_type == "Upload File":
            file = st.file_uploader(
                "Upload File",
                type=["jpg", "jpeg", "png", "gif", "mp4", "mov"],
            )
            if file:
                file_path = save_upload(file, subfolder='media')
        elif source_type == "YouTube Video":
            file_path = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
            )
        elif source_type == "Photo Link":
            file_path = st.text_input(
                "Photo URL",
                placeholder="https://example.com/photo.jpg",
            )
        elif source_type == "Video Link":
            file_path = st.text_input(
                "Video URL",
                placeholder="https://example.com/video.mp4",
            )

        submitted = st.form_submit_button("Upload")
        if submitted and title and file_path:
            execute_write(
                "INSERT INTO media (title, media_type, file_path, caption, tags, related_type, related_id, uploaded_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (title, media_type, file_path, caption or None, tags or None,
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
    edit_media_type = st.selectbox(
        "Type",
        ["photo", "video"],
        index=0 if edit_item['media_type'] == 'photo' else 1,
        key="edit_media_type",
    )
    with st.form("edit_media"):
        edit_title = st.text_input("Title*", value=edit_item['title'])

        # Determine current source type from existing file_path
        old_fp = edit_item['file_path']
        old_is_url = is_url(old_fp)
        if old_is_url:
            if is_youtube_url(old_fp):
                existing_source = "YouTube Video"
            elif edit_media_type == 'photo':
                existing_source = "Photo Link"
            else:
                existing_source = "Video Link"
        else:
            existing_source = "Upload File"

        # Source options based on media type
        if edit_media_type == "photo":
            edit_source_options = ["Upload File", "Photo Link"]
        else:
            edit_source_options = ["Upload File", "YouTube Video", "Video Link"]
        edit_source_type = st.radio(
            "Source",
            edit_source_options,
            horizontal=True,
            index=edit_source_options.index(existing_source)
                  if existing_source in edit_source_options else 0,
            label_visibility="collapsed",
        )

        edit_caption = st.text_area("Caption", value=edit_item.get('caption') or "")
        edit_tags = st.text_input("Tags (comma separated)", value=edit_item.get('tags') or "")
        edit_related_type = st.selectbox(
            "Related to",
            ["general", "project", "member"],
            index=(["general", "project", "member"].index(edit_item['related_type'])
                   if edit_item['related_type'] in ("general", "project", "member")
                   else 0),
        )
        edit_related_id = st.number_input(
            "Related ID (optional)", min_value=0, value=edit_item['related_id'] or 0,
        )

        new_file_path = None
        if edit_source_type == "Upload File":
            edit_file = st.file_uploader(
                "Upload New File (optional)",
                type=["jpg", "jpeg", "png", "gif", "mp4", "mov"],
            )
            if edit_file:
                new_file_path = save_upload(edit_file, subfolder='media')
                if old_fp and not old_is_url:
                    delete_file(old_fp)
            else:
                new_file_path = old_fp
        elif edit_source_type == "YouTube Video":
            new_file_path = st.text_input(
                "YouTube URL",
                value=old_fp if (old_is_url and is_youtube_url(old_fp)) else "",
                placeholder="https://www.youtube.com/watch?v=...",
            )
        elif edit_source_type == "Photo Link":
            new_file_path = st.text_input(
                "Photo URL",
                value=old_fp if old_is_url else "",
                placeholder="https://example.com/photo.jpg",
            )
        elif edit_source_type == "Video Link":
            new_file_path = st.text_input(
                "Video URL",
                value=old_fp if old_is_url else "",
                placeholder="https://example.com/video.mp4",
            )

        edit_submitted = st.form_submit_button("Update Media")
        if edit_submitted and edit_title:
            if edit_source_type != "Upload File" and not new_file_path:
                st.error("Please enter a URL for the selected source type.")
                st.stop()
            execute_write(
                "UPDATE media SET title=%s, media_type=%s, file_path=%s, caption=%s, tags=%s, related_type=%s, related_id=%s WHERE id=%s",
                (edit_title, edit_media_type, new_file_path, edit_caption or None,
                 edit_tags or None,
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
            fp = r['file_path']
            try:
                st.image(fp, caption=r.get('caption'), use_container_width=True)
            except Exception as e:
                st.warning(f"Could not display photo: {e}")
                if is_url(fp):
                    st.link_button("View Photo", fp)
            st.write(f"**Tags:** {r.get('tags') or '-'}")
            st.write(f"**Related:** {r.get('related_type')} {r.get('related_id') or ''}")
            st.write(f"**Source:** {'Link' if is_url(fp) else 'Uploaded File'}")
            if user_role in ('admin', 'editor'):
                if st.button("Delete", key=f"del_media_{r['id']}", type='secondary'):
                    if not is_url(fp):
                        delete_file(fp)
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

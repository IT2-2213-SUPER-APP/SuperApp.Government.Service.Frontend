# Roles & Permissions

- Owner: full control, manage members, files, metadata, visibility.
- Editor: can add/replace/remove files and folders; cannot delete submission or manage members.
- Viewer: can read if submission not otherwise restricted.

Blocking:
- Profile.blocked_users prevents the blocked user from viewing owner's submissions/profile.

Visibility:
- PUBLIC: visible to all (respecting registered_only).
- PRIVATE: owner + members only.
- LINK_ONLY: accessible via slug link (respecting registered_only for guests when false). Note: expand per product spec.
- registered_only: boolean; if true, guests cannot view even PUBLIC content.

API endpoints (selected):
- Submissions: /api/submissions/ (list/create), /api/submissions/{id}/ (retrieve/update/delete)
- Members (owner-only): /api/submissions/{id}/members/, add_member/, remove_member/
- Files: /api/submissions/{id}/files/
- Folders: /api/submissions/{id}/folders/
- Votes: /api/submissions/{id}/(upvote|downvote|clear_vote|votes)/
- Reports: /api/submissions/{id}/report/

# Rate Limits

Configured via .env and read by settings:

- SUBMISSION_CREATE_COOLDOWN_SECONDS (default 32s)
- SUBMISSION_EDIT_COOLDOWN_SECONDS (default 16s)
- COMMENT_COOLDOWN_SECONDS (default 8s)
- MESSAGE_COOLDOWN_SECONDS (default 2s)

Applied using django-ratelimit decorators.

Notes:
- 429 is returned when threshold exceeded.
- Limits are per user (fallback to IP for anonymous where applicable).

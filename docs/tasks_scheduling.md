# Tasks & Scheduling

- Weekly cleanup: hard-delete soft-deleted submissions older than 30 days (core.tasks.cleanup_soft_deleted).
- Weekly trending: recompute trending_score using Wilson LB over last 7 days (submissions.tasks.recalculate_trending).

Configured in settings via CELERY_BEAT_SCHEDULE; uses Redis as broker/result.

Run locally (optional during dev):
```sh
poetry run celery -A config worker -l info
poetry run celery -A config beat -l info
```

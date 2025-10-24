# Architecture

```mermaid
flowchart LR
  Client -->|HTTP/JSON| DRF[API Layer]
  DRF --> Auth[JWT/Session]
  DRF --> Submissions
  DRF --> Comments
  DRF --> Messaging
  DRF --> Users
  Submissions -->|ORM| Postgres[(Postgres)]
  Comments -->|ORM| Postgres
  Messaging -->|ORM| Postgres
  Users -->|ORM| Postgres
  DRF --> Celery
  Celery --> Redis[(Redis Broker/Result)]
```

Key flows:
- Upload: create submission -> upload files -> organize into folders.
- Visibility: PUBLIC/PRIVATE/LINK_ONLY + registered_only flag.
- Roles: owner/editor/viewer per submission; owner manages members.
- Voting: per-user up/down; rating derived; trending via Wilson LB.
- Reports: stored and triaged in admin only.

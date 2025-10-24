# Data Model

```mermaid
erDiagram
  User ||--o{ Profile : has
  User ||--o{ Submission : owns
  Submission ||--o{ SubmissionFile : contains
  Submission ||--o{ Folder : has
  Folder ||--o{ Folder : children
  Folder ||--o{ SubmissionFile : contains
  Submission ||--o{ SubmissionVote : has
  Submission ||--o{ SubmissionReport : has
  Submission ||--o{ Comment : has
  Submission ||--o{ SubmissionMember : has
  User ||--o{ SubmissionMember : joins
  User ||--o{ SubmissionVote : casts
  User ||--o{ SubmissionReport : files
  User ||--o{ Comment : writes
  User ||--o{ Message : sends
  User ||--o{ Message : receives
```

- Profile: blocked_users M2M to User, badges via flags/is_staff/is_superuser.
- Submission: slug (unique, case-insensitive), registered_only, trending_score.
- SubmissionMember: role in {editor, viewer}.
- Folder: hierarchical, unique (submission,parent,name).
- SubmissionFile: optional folder, stored under submissions/<slug>/path.
- SubmissionVote: value in {+1, -1}.
- SubmissionReport: admin-triaged status.

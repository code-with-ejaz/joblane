JOBLANE
Files: index.html (site), ingest.py (fetches jobs), jobs.json (output), gov-jobs.json (Pakistan government jobs you add by hand),
.github/workflows/ingest.yml (runs ingest.py every 3 hours).

Update steps: in your GitHub repo, upload/replace index.html and ingest.py, add gov-jobs.json, then Actions > ingest-jobs > Run workflow.

gov-jobs.json format (one object per job, copy details from the official portal and keep its link):
[{"title":"Assistant Director","department":"Ministry of X","location":"Islamabad, Pakistan",
  "apply":"https://official-portal/link","posted":"2026-10-25","salary":"BPS-17","description":"Short summary of the post and last date."}]

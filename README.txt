JOBLANE SETUP (about 10 minutes, all free)
1. Create a free GitHub account and a new PUBLIC repository named joblane.
2. Upload every file in this folder, including the .github folder (drag the whole folder in).
3. Edit ingest.py and put your real email in the User-Agent line.
4. In the repo go to Actions > ingest-jobs > Run workflow. After about a minute jobs.json fills with live jobs.
5. Go to Cloudflare Pages > Create project > Connect to Git > pick the repo. Build command: none. Output directory: /
6. Your site goes live on a yourname.pages.dev address and updates itself whenever jobs.json changes.

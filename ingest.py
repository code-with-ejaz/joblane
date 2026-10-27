import json, re, requests, datetime as dt

H = {"User-Agent": "Joblane/1.0 (contact: you@example.com)"}  # put your real email here
clean = lambda s: re.sub(r"<[^>]+>", " ", s or "")
excerpt = lambda s: " ".join(clean(s).split())[:240]
jobs = []

def remotive():
    r = requests.get("https://remotive.com/api/remote-jobs", headers=H, timeout=30).json()
    for j in r.get("jobs", []):
        jobs.append(dict(title=j["title"], company=j["company_name"],
            location=j.get("candidate_required_location") or "Remote",
            category=j.get("category") or "Other",
            type=(j.get("job_type") or "full_time").replace("_", "-").title(), remote=True,
            skills=j.get("tags", [])[:5], summary=excerpt(j.get("description")),
            source="Remotive", apply=j["url"], posted=j["publication_date"][:10],
            salary=j.get("salary") or ""))

def arbeitnow():
    r = requests.get("https://www.arbeitnow.com/api/job-board-api", headers=H, timeout=30).json()
    for j in r.get("data", []):
        jobs.append(dict(title=j["title"], company=j["company_name"],
            location=j.get("location") or "Europe",
            category=(j.get("tags") or ["Other"])[0],
            type=(j.get("job_types") or ["Full-time"])[0], remote=j.get("remote", False),
            skills=(j.get("tags") or [])[:5], summary=excerpt(j.get("description")),
            source="Arbeitnow", apply=j["url"],
            posted=dt.datetime.fromtimestamp(j["created_at"]).strftime("%Y-%m-%d"), salary=""))

def remoteok():
    r = requests.get("https://remoteok.com/api", headers=H, timeout=30).json()[1:]  # item 0 is a legal notice
    for j in r:
        jobs.append(dict(title=j["position"], company=j["company"],
            location=j.get("location") or "Remote", category="Software",
            type="Full-time", remote=True, skills=j.get("tags", [])[:5],
            summary=excerpt(j.get("description")), source="RemoteOK",
            apply=j["url"], posted=j["date"][:10], salary=""))

for fn in (remotive, arbeitnow, remoteok):
    try: fn()
    except Exception as e: print("failed:", fn.__name__, e)

seen, out = set(), []
for j in jobs:
    k = (j["title"].lower(), j["company"].lower(), j["location"].lower())
    if k not in seen and j.get("apply"):
        seen.add(k); out.append(j)

if out:  # never overwrite good data with an empty result
    json.dump(out, open("jobs.json", "w"), ensure_ascii=False)
print("saved", len(out))

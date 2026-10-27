"""Joblane ingestion: legal public APIs only. Run by GitHub Actions every 3 hours."""
import json, re, html, os, time, requests, datetime as dt

H = {"User-Agent": "Joblane/1.0 (contact: you@example.com)"}  # put your real email here
MAX_AGE_DAYS, MAX_JOBS = 45, 1500
GREENHOUSE_BOARDS = ["stripe", "airbnb", "cloudflare", "figma"]  # add any company that uses Greenhouse

def text(s):
    s = html.unescape(s or "")
    s = re.sub(r"</(p|div|li|h\d)>|<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n\n", s).strip()

def cut(s, n):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"

REGIONS = [
 ("USA", r"\b(united states|usa|u\.s\.|us|america|new york|california|texas|san francisco|seattle|austin|boston|chicago)\b"),
 ("UK", r"\b(united kingdom|uk|england|scotland|wales|london|manchester)\b"),
 ("Canada", r"\b(canada|toronto|vancouver|montreal)\b"),
 ("Pakistan", r"\b(pakistan|karachi|lahore|islamabad|rawalpindi|faisalabad|peshawar|quetta)\b"),
 ("India", r"\b(india|bangalore|bengaluru|mumbai|delhi|hyderabad|pune|chennai)\b"),
 ("Europe", r"\b(europe|emea|germany|france|spain|italy|netherlands|portugal|poland|ireland|sweden|norway|denmark|finland|austria|switzerland|belgium|berlin|munich|hamburg|amsterdam|paris|madrid|barcelona|lisbon|dublin|vienna|zurich|czech|romania|estonia|greece)\b"),
]
def region(loc, remote):
    l = (loc or "").lower()
    for name, p in REGIONS:
        if re.search(p, l): return name
    return "Remote" if remote or re.search(r"anywhere|worldwide|remote|global|^$", l) else "Other"

CATS = [
 ("Software Development", r"developer|engineer|software|devops|backend|frontend|full.?stack|programmer|\bqa\b|\bsre\b|android|\bios\b|web "),
 ("Data & AI", r"\bdata\b|machine learning|\bai\b|analyst|scientist|analytics|\bml\b"),
 ("Design", r"design|\bux\b|\bui\b|creative|illustrat"),
 ("Product", r"product manager|product owner|program manager|project manager"),
 ("Marketing", r"market|\bseo\b|growth|social media|brand|community"),
 ("Sales", r"sales|account executive|business development|partnership"),
 ("Customer Support", r"support|customer success|customer service|helpdesk"),
 ("Writing & Content", r"writer|content|editor|copy|translator"),
 ("Finance", r"financ|accountant|accounting|bookkeep|payroll|audit"),
 ("HR & Recruiting", r"recruit|talent|\bhr\b|people ops|human resources"),
 ("Education", r"teacher|tutor|instructor|lecturer|education"),
 ("Operations", r"operations|admin|assistant|logistics|coordinator|manager"),
]
def category(title, extra=""):
    for src in (title or "", extra or ""):
        s = src.lower().replace("-", " ")
        for name, p in CATS:
            if re.search(p, s): return name
    return "Other"

def jtype(s):
    s = (s or "").lower()
    if "part" in s: return "Part-time"
    if "contract" in s or "freelance" in s: return "Contract"
    if "intern" in s: return "Internship"
    return "Full-time"

def day(v):
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v / 1000 if v > 1e12 else v).strftime("%Y-%m-%d")
    return str(v or "")[:10]

def salary(lo, hi, cur="USD"):
    try:
        if lo and hi: return f"{cur} {int(lo):,}–{int(hi):,}"
        if lo or hi: return f"{cur} {int(lo or hi):,}"
    except Exception: pass
    return ""

jobs = []
def add(source, title, company, logo, loc, remote, ctype, cat_extra, tags, desc, apply, posted, sal=""):
    d = text(desc)
    jobs.append(dict(title=title, company=company or "Company", logo=logo or "",
        location=loc or "Remote", region=region(loc, remote), remote=bool(remote),
        category=category(title, cat_extra), type=jtype(ctype), skills=(tags or [])[:6],
        summary=cut(d.replace("\n", " "), 200), description=cut(d, 1500),
        source=source, apply=apply, posted=day(posted), salary=sal))

def remotive():
    for j in requests.get("https://remotive.com/api/remote-jobs", headers=H, timeout=30).json().get("jobs", []):
        add("Remotive", j["title"], j["company_name"], j.get("company_logo"), j.get("candidate_required_location"),
            True, j.get("job_type"), j.get("category"), j.get("tags"), j.get("description"), j["url"],
            j["publication_date"], j.get("salary") or "")

def arbeitnow():
    for j in requests.get("https://www.arbeitnow.com/api/job-board-api", headers=H, timeout=30).json().get("data", []):
        add("Arbeitnow", j["title"], j["company_name"], "", j.get("location"), j.get("remote", False),
            " ".join(j.get("job_types") or []), " ".join(j.get("tags") or []), j.get("tags"),
            j.get("description"), j["url"], j["created_at"])

def remoteok():
    for j in requests.get("https://remoteok.com/api", headers=H, timeout=30).json()[1:]:  # item 0 = legal notice
        add("RemoteOK", j["position"], j["company"], j.get("company_logo") or j.get("logo"), j.get("location"),
            True, "", " ".join(j.get("tags") or []), j.get("tags"), j.get("description"), j["url"], j["date"])

def himalayas():
    for off in range(0, 400, 20):  # 20 jobs per request, max allowed
        r = requests.get("https://himalayas.app/jobs/api", params={"limit": 20, "offset": off}, headers=H, timeout=30).json()
        batch = r.get("jobs", [])
        if not batch: break
        for j in batch:
            locs = j.get("locationRestrictions") or []
            add("Himalayas", j["title"], j.get("companyName"), j.get("companyLogo"), ", ".join(locs) or "Worldwide",
                True, j.get("employmentType"), " ".join(j.get("categories") or []), j.get("categories"),
                j.get("description") or j.get("excerpt"), j.get("applicationLink") or j.get("guid"), j.get("pubDate"),
                salary(j.get("minSalary"), j.get("maxSalary"), j.get("currency") or "USD"))
        time.sleep(0.6)

def greenhouse():
    for b in GREENHOUSE_BOARDS:
        try:
            r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true", headers=H, timeout=30).json()
            for j in r.get("jobs", []):
                loc = (j.get("location") or {}).get("name", "")
                add("Greenhouse", j["title"], b.title(), "", loc, "remote" in loc.lower(), "", " ".join(d["name"] for d in j.get("departments", [])),
                    [], j.get("content"), j["absolute_url"], j.get("updated_at"))
        except Exception as e: print("failed board", b, e)

def pakistan_gov():
    """Reads gov-jobs.json, which you fill by hand from official portals (FPSC, PPSC, NTS, ministry sites)."""
    if not os.path.exists("gov-jobs.json"): return
    for j in json.load(open("gov-jobs.json")):
        add("Pakistan Govt", j["title"], j.get("department", "Government of Pakistan"), "", j.get("location", "Pakistan"),
            False, j.get("type", "Full-time"), "government", ["Government"], j.get("description", ""), j["apply"],
            j.get("posted") or dt.date.today().isoformat(), j.get("salary", ""))
        jobs[-1]["category"], jobs[-1]["region"] = "Government", "Pakistan"

for fn in (remotive, arbeitnow, remoteok, himalayas, greenhouse, pakistan_gov):
    try: fn(); print("ok", fn.__name__, len(jobs))
    except Exception as e: print("failed:", fn.__name__, e)

cutoff = (dt.date.today() - dt.timedelta(days=MAX_AGE_DAYS)).isoformat()
seen, out = set(), []
for j in sorted(jobs, key=lambda x: x["posted"], reverse=True):
    k = (j["title"].lower(), j["company"].lower(), j["location"].lower())
    if k in seen or not j["apply"] or not j["posted"] or j["posted"] < cutoff: continue
    seen.add(k); out.append(j)
out = out[:MAX_JOBS]
if out:  # never overwrite good data with an empty result
    json.dump(out, open("jobs.json", "w"), ensure_ascii=False)
print("saved", len(out))

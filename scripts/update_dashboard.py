#!/usr/bin/env python3
"""Generate a live-data SVG dashboard using GitHub's public REST API."""
import json, os, time, urllib.request, urllib.error
from html import escape
from pathlib import Path

USER = os.environ.get("GITHUB_USERNAME", "raghav4444")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = Path("assets/dashboard.svg")
API = "https://api.github.com"

def get_json(url):
    headers = {"Accept":"application/vnd.github+json", "User-Agent":"NeoTerminal-Profile-README"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as res:
        return json.load(res)

def esc(x):
    return escape(str(x), quote=True)

def shorten(x, n=25):
    x = str(x or "")
    return x if len(x) <= n else x[:n-1] + "…"

def make_svg(profile, repos, langs, events):
    name = profile.get("name") or USER
    location = profile.get("location") or "Location not set"
    bio = profile.get("bio") or "Building useful products"
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    repos_count = profile.get("public_repos", len(repos))
    followers = profile.get("followers", 0)
    updated = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    lang_list = sorted(langs.items(), key=lambda item: item[1], reverse=True)[:4]
    total = sum(v for _, v in lang_list) or 1
    lang_svg = []
    colors = ["#34d399", "#a3e635", "#60a5fa", "#fb923c"]
    for i, (lang, amount) in enumerate(lang_list):
        y = 522 + i * 22
        width = max(4, round(150 * amount / total))
        lang_svg.append(
            f'<text x="760" y="{y}" class="mono tiny white">{esc(shorten(lang, 12))}</text>'
            f'<rect x="850" y="{y-10}" width="150" height="8" rx="2" fill="#0b3325"/>'
            f'<rect x="850" y="{y-10}" width="{width}" height="8" rx="2" fill="{colors[i]}"/>'
            f'<text x="1008" y="{y}" class="mono tiny muted">{round(amount*100/total)}%</text>'
        )
    while len(lang_svg) < 4:
        lang_svg.append(f'<text x="760" y="{522+len(lang_svg)*22}" class="mono tiny muted">No language data</text>')

    candidates = [r for r in repos if not r.get("fork") and r.get("name") != USER]
    candidates.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("updated_at", "")), reverse=True)
    project_svg = []
    colors = ["#34d399", "#fbbf24", "#f472b6"]
    for i, repo in enumerate(candidates[:3]):
        y = 458 + i * 27
        project_svg.append(
            f'<rect x="25" y="{y-10}" width="11" height="11" rx="2" fill="{colors[i]}"/>'
            f'<text x="45" y="{y}" class="mono small white">{esc(shorten(repo.get("name", "repo"), 20))}</text>'
            f'<text x="195" y="{y}" class="mono tiny muted">★ {repo.get("stargazers_count",0)} ⑂ {repo.get("forks_count",0)}</text>'
        )
    if not project_svg:
        project_svg.append('<text x="25" y="458" class="mono small muted">No public repositories found</text>')

    event_lines = []
    for event in events[:3]:
        kind = event.get("type", "Activity").replace("Event", "")
        repo = event.get("repo", {}).get("name", "").split("/")[-1]
        event_lines.append(f'<text x="827" y="{195+len(event_lines)*13}" class="mono tiny white">{esc(shorten(kind + ": " + repo, 31))}</text>')
    while len(event_lines) < 3:
        event_lines.append(f'<text x="827" y="{195+len(event_lines)*13}" class="mono tiny white">Keep shipping code</text>')

    bars = ''.join(
        f'<rect x="{329+i*15}" y="{578-((i*7+stars*3)%31)}" width="11" height="{((i*7+stars*3)%31)+5}"/>'
        for i in range(25)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620" role="img">
<title>NeoTerminal OS — {esc(name)}</title>
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#03100c"/><stop offset=".55" stop-color="#061611"/><stop offset="1" stop-color="#020806"/></linearGradient>
 <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#071b15"/><stop offset="1" stop-color="#04100d"/></linearGradient>
 <pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#123329" stroke-width=".6" opacity=".55"/></pattern>
 <style>.mono{{font-family:Consolas,'Liberation Mono',monospace}} .ui{{font-family:Arial,sans-serif}} .green{{fill:#34d399}} .muted{{fill:#8aa69a}} .white{{fill:#e2eee8}} .tiny{{font-size:11px}} .small{{font-size:13px}} .panel{{fill:url(#panel);stroke:#174333;stroke-width:1.2}} .rule{{stroke:#174333;stroke-width:1}}</style>
</defs>
<rect x="1" y="1" width="1098" height="618" rx="12" fill="url(#bg)" stroke="#1b4938" stroke-width="2"/>
<rect x="2" y="2" width="1096" height="30" rx="11" fill="#07120f"/><path d="M2 31H1098" stroke="#1b4938"/>
<circle cx="18" cy="16" r="5" fill="#fb7185"/><circle cx="34" cy="16" r="5" fill="#fbbf24"/><circle cx="50" cy="16" r="5" fill="#34d399"/>
<text x="68" y="20" class="mono tiny" fill="#1d7757">NEOTERM // LIVE DATA</text><text x="830" y="20" class="mono tiny muted">UPDATED {esc(updated)}</text>
<rect x="12" y="42" width="170" height="564" rx="8" class="panel"/>
<circle cx="32" cy="63" r="11" fill="#e2eee8"/><text x="50" y="67" class="ui" font-size="14" font-weight="700" fill="#e2eee8">{esc(USER)}</text><path d="M12 82H182" class="rule"/>
<rect x="20" y="93" width="154" height="30" rx="5" fill="#0d3326" stroke="#176b4a"/><text x="31" y="112" class="mono small green">▣  home</text>
<text x="31" y="146" class="mono small muted">◎  about</text><text x="31" y="178" class="mono small muted">▤  projects</text><text x="31" y="210" class="mono small muted">◇  skills</text><text x="31" y="242" class="mono small muted">▥  stats</text><text x="31" y="274" class="mono small muted">♜  achievements</text><text x="31" y="306" class="mono small muted">◷  activity</text><text x="31" y="338" class="mono small muted">✉  contact</text>
<path d="M24 365H170" class="rule"/><text x="26" y="389" class="mono tiny" fill="#267d5b">PUBLIC REPOS</text><text x="26" y="418" class="mono" font-size="24" fill="#e2eee8">{repos_count}</text><text x="26" y="438" class="mono tiny muted">repositories</text><text x="26" y="472" class="mono tiny muted">FOLLOWERS</text><text x="26" y="500" class="mono" font-size="22" fill="#e2eee8">{followers}</text><text x="26" y="575" class="mono tiny muted">AUTO-REFRESH ENABLED</text>
<rect x="194" y="42" width="590" height="374" rx="8" class="panel"/><rect x="194" y="42" width="590" height="32" rx="8" fill="#0a2018"/><path d="M194 74H784" class="rule"/><circle cx="211" cy="58" r="4" fill="#fbbf24"/><circle cx="223" cy="58" r="4" fill="#34d399"/><text x="238" y="62" class="mono tiny green">{esc(USER)}@github:~</text>
<rect x="204" y="82" width="570" height="324" fill="url(#grid)" opacity=".65"/><rect x="207" y="91" width="205" height="280" rx="5" fill="#03100c" stroke="#123c2c"/><text x="220" y="108" class="mono tiny" fill="#16885f">IDENTITY_RENDER.exe</text>
<g class="mono" fill="#34d399" font-size="9.2">
<text x="225" y="132">          .:::::::.</text><text x="225" y="143">       .::░░░░░░░::.</text><text x="225" y="154">      :░░░░░░░░░░░░:</text><text x="225" y="165">     :░░░░░░░░░░░░░░:</text><text x="225" y="176">     ░░░  ░░░░░  ░░░</text><text x="225" y="187">     ░░░  ░░░░░  ░░░</text><text x="225" y="198">      ░░░░░░░░░░░░░</text><text x="225" y="209">       ░░░░░░░░░░░</text><text x="225" y="220">         ░░░░░░░</text><text x="225" y="231">       .░░░░░░░░░.</text><text x="225" y="242">    .░░░░░░░░░░░░░░.</text><text x="225" y="253">  .░░░░░░░░░░░░░░░░░░.</text><text x="225" y="264"> ░░░░░░░░░░░░░░░░░░░░░</text><text x="225" y="275"> ░░░░░░░░░░░░░░░░░░░░░</text><text x="225" y="286">  ░░░░░░░░░░░░░░░░░░░</text><text x="225" y="297">   ░░░░░░░░░░░░░░░░░</text><text x="225" y="308">    ░░░░░░░░░░░░░░░</text><text x="225" y="319">      ░░░░░░░░░░░</text><text x="225" y="330">        ░░░░░░░</text>
</g><text x="221" y="350" class="mono tiny muted">[ public profile loaded ]</text>
<text x="430" y="105" class="mono small green">$ whoami</text><text x="430" y="130" class="mono small muted">Name</text><text x="506" y="130" class="mono small white">{esc(shorten(name,24))}</text>
<text x="430" y="153" class="mono small muted">Role</text><text x="506" y="153" class="mono small white">Full Stack Developer</text><text x="430" y="176" class="mono small muted">Location</text><text x="506" y="176" class="mono small white">{esc(shorten(location,24))}</text>
<text x="430" y="199" class="mono small muted">Repos</text><text x="506" y="199" class="mono small green">{repos_count} public repositories</text><text x="430" y="222" class="mono small muted">Stars</text><text x="506" y="222" class="mono small green">{stars} total repository stars</text><text x="430" y="245" class="mono small muted">Forks</text><text x="506" y="245" class="mono small white">{forks} total repository forks</text>
<text x="430" y="277" class="mono small green">$ cat profile_bio.txt</text><text x="430" y="301" class="mono small white">{esc(shorten(bio,31))}</text><text x="430" y="322" class="mono small white">Build useful things.</text><text x="430" y="343" class="mono small white">Learn relentlessly.</text><rect x="430" y="363" width="8" height="15" fill="#34d399"/>
<rect x="796" y="42" width="292" height="184" rx="8" class="panel"/><rect x="796" y="42" width="292" height="32" rx="8" fill="#0a2018"/><text x="812" y="62" class="mono small green">◆ system</text>
<rect x="814" y="83" width="254" height="58" rx="4" fill="#03100c" stroke="#123c2c"/><g fill="#34d399" font-size="8.5" class="mono"><text x="822" y="96">░░░░░░░░░░░░░░░░░░░░░░</text><text x="822" y="106">░░░░░░░░░░░░░░░░░░░░░░</text><text x="822" y="116">░░░░░░░░░░░░░░░░░░░░░░</text><text x="822" y="126">░░░░░░░░░░░░░░░░░░░░░░</text><text x="822" y="136">░░░░░░░░░░░░░░░░░░░░░░</text></g>
<circle cx="818" cy="157" r="3" fill="#34d399"/><text x="829" y="161" class="mono tiny white">{followers} followers</text><text x="814" y="181" class="mono tiny muted">› Recent public activity</text>{''.join(event_lines)}
<g><rect x="194" y="428" width="140" height="38" rx="6" fill="#092017" stroke="#176044"/><text x="211" y="452" class="mono small green">〈/〉 Projects</text><rect x="343" y="428" width="145" height="38" rx="6" fill="#092017" stroke="#176044"/><text x="359" y="452" class="mono small green">◉ GitHub Stats</text><rect x="497" y="428" width="135" height="38" rx="6" fill="#092017" stroke="#176044"/><text x="511" y="452" class="mono small green">◈ Tech Stack</text><rect x="641" y="428" width="143" height="38" rx="6" fill="#092017" stroke="#176044"/><text x="654" y="452" class="mono small green">♜ Achievements</text></g>
<rect x="12" y="480" width="290" height="126" rx="8" class="panel"/><text x="25" y="500" class="mono small green">repositories --popular</text><path d="M12 509H302" class="rule"/>{''.join(project_svg)}
<rect x="313" y="480" width="423" height="126" rx="8" class="panel"/><text x="327" y="500" class="mono small green">github_stats</text><path d="M313 509H736" class="rule"/><text x="329" y="536" class="mono" font-size="21" fill="#e2eee8">{repos_count}</text><text x="329" y="551" class="mono tiny muted">Public repos</text><text x="430" y="535" class="mono" font-size="20" fill="#e2eee8">{stars}</text><text x="430" y="551" class="mono tiny muted">Stars</text><text x="505" y="535" class="mono" font-size="20" fill="#e2eee8">{forks}</text><text x="505" y="551" class="mono tiny muted">Forks</text><text x="589" y="535" class="mono" font-size="20" fill="#e2eee8">{followers}</text><text x="589" y="551" class="mono tiny muted">Followers</text><g fill="#0f513a">{bars}</g>
<rect x="747" y="480" width="341" height="126" rx="8" class="panel"/><text x="761" y="500" class="mono small green">languages // byte totals</text><path d="M747 509H1088" class="rule"/>{''.join(lang_svg)}
</svg>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")

def main():
    profile = get_json(f"{API}/users/{USER}")
    repos = get_json(f"{API}/users/{USER}/repos?per_page=100&sort=updated")
    events = get_json(f"{API}/users/{USER}/events/public?per_page=10")
    languages = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            for lang, size in get_json(repo["languages_url"]).items():
                languages[lang] = languages.get(lang, 0) + size
    except (urllib.error.URLError, TimeoutError):
        pass
    make_svg(profile, repos, languages, events)
    print(f"Updated {OUT} for {USER}: {len(repos)} repositories.")

if __name__ == "__main__":
    main()

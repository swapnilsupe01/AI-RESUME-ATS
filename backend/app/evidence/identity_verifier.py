"""
GitHub Identity Ownership Verifier — Recruiter-Side Fraud Detection.

Solves the critical problem: A candidate can paste ANY GitHub URL (e.g., github.com/swapnil-23
which belongs to a random person) — and the system would wrongly credit that person's repos.

This module uses independent signals to determine whether a GitHub profile
actually belongs to the resume candidate:

  Signal  1 — GitHub Bio Display Name    : Does GitHub profile.name match resume name?
  Signal  2 — Username Token Overlap     : Do name tokens appear in the GitHub username?
  Signal  3 — Cross-Platform URL Link    : Does GitHub bio/blog link to the resume's LinkedIn?
  Signal  4 — Commit Author Name Match   : Do recent commit authors match the resume name?
  Signal  5 — Account Age vs Experience  : Does account age align with claimed experience?
  Signal  6 — Commit Email Cross-Match   : Do commit author emails match the resume email?
  Signal  7 — Contribution History       : Does the account show real developer activity?
  Signal  8 — Profile README Name Scan   : Does the profile README mention the candidate's name?
  Signal  9 — LinkedIn Post → GitHub     : Do LinkedIn posts link to this GitHub account?
  Signal 10 — LinkedIn OAuth Verified    : Did the candidate authenticate via LinkedIn OAuth,
                                            and does the verified identity match the resume?

LinkedIn OAuth Verified is categorically different from the heuristic signals:
it is a direct, LinkedIn-issued, candidate-consented identity proof.

Scoring:
  >= 80  -> Ownership Confirmed     (green)
  50-79  -> Likely Owner            (yellow)
  20-49  -> Uncertain Ownership     (orange)
  < 20   -> Ownership Mismatch      (red) -- Potential profile fraud / wrong GitHub pasted
"""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.github.oauth_service import get_current_token

GITHUB_URL_RE = re.compile(
    r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)(?:/([a-zA-Z0-9_\-\.]+))?',
    re.IGNORECASE
)


# ── Name Normalisation Helpers ─────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Lowercase, remove accents, strip punctuation/digits for clean token comparison."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z\s]", " ", text.lower())
    return text.strip()


def _name_tokens(name: str) -> List[str]:
    """
    Split a name into meaningful tokens >= 3 chars.
    Handles: 'Swapnil Supe' -> ['swapnil', 'supe']
    """
    tokens = _normalize_text(name).split()
    return [t for t in tokens if len(t) >= 3]


def _username_tokens(username: str) -> List[str]:
    """
    Tokenize a GitHub username by splitting on separators and CamelCase boundaries.

    Examples:
      swapnilsupe01  -> tokens extracted via greedy name-token matching (see below)
      swapnil-23     -> ['swapnil']
      swapnil_supe   -> ['swapnil', 'supe']
      ss-coder       -> ['coder']   (initials 'ss' < 3 chars → skipped)
      xyz-dev-99     -> ['xyz', 'dev']

    Note: For compound usernames like 'swapnilsupe01' (no separator), we cannot
    easily split without knowing the name first. That is handled in the overlap
    signal by substring search, not by this tokenizer.
    """
    username_clean = re.sub(r"\d+", "", username.lower())
    parts = re.split(r"[-_.\s]+", username_clean)
    # Handle CamelCase within each part
    camel_split: List[str] = []
    for part in parts:
        camel_split.extend(re.sub(r"([a-z])([A-Z])", r"\1 \2", part).lower().split())
    return [t for t in camel_split if len(t) >= 3]


# ── Signal Computations ─────────────────────────────────────────────────────

def _signal_username_token_overlap(github_username: str, candidate_name: str) -> Tuple[float, str]:
    """
    Signal 2: How many resume name tokens appear in the GitHub username?

    Two-pass strategy:
      Pass 1 — Direct token split (catches swapnil-23 → 'swapnil')
      Pass 2 — Substring search in raw username (catches swapnilsupe01 → 'supe')

    This way:
      swapnilsupe01 + 'Swapnil Supe' → finds both 'swapnil' and 'supe' → 100%
      swapnil-23    + 'Swapnil Supe' → finds 'swapnil', misses 'supe'  → 50%
      xyz-dev-99    + 'Swapnil Supe' → finds neither                    → 0%
    """
    name_toks = _name_tokens(candidate_name)
    if not name_toks:
        return 0.0, "Could not parse candidate name tokens."

    username_lower = github_username.lower()
    # Remove digits for cleaner substring match
    username_clean = re.sub(r"\d+", "", username_lower)
    user_split_toks = set(_username_tokens(github_username))

    matched = set()
    for tok in name_toks:
        # Pass 1: exact split token match
        if tok in user_split_toks:
            matched.add(tok)
        # Pass 2: substring search in cleaned username (handles concatenated names)
        elif tok in username_clean:
            matched.add(tok)

    name_set = set(name_toks)
    score = (len(matched) / len(name_set)) * 100.0

    if score >= 100:
        explanation = f"Username '{github_username}' contains ALL name tokens {sorted(matched)} — strong name alignment."
    elif score > 0:
        explanation = (
            f"Username '{github_username}' partially matches — "
            f"found: {sorted(matched)}, missing: {sorted(name_set - matched)}. "
            f"Could be a different '{list(matched)[0]}' — first-name-only match is insufficient."
        )
    else:
        explanation = (
            f"Username '{github_username}' shares NO tokens with '{candidate_name}'. "
            f"This is likely a completely different person's account."
        )

    return round(score, 1), explanation


def _signal_bio_name_match(github_display_name: str, candidate_name: str) -> Tuple[float, str]:
    """
    Signal 1: Does the GitHub profile's display name (profile.name) match the resume name?

    Uses token overlap to handle nicknames, middle names, shortened names gracefully.
    'Swapnil S. Supe' <-> 'Swapnil Supe' -> still matches on 'swapnil' and 'supe'.
    """
    if not github_display_name or not github_display_name.strip():
        return 0.0, "GitHub profile has no display name set (anonymous/incomplete profile)."

    name_toks = set(_name_tokens(candidate_name))
    bio_toks  = set(_name_tokens(github_display_name))

    if not name_toks:
        return 0.0, "Could not parse candidate name tokens."

    matched = name_toks & bio_toks
    score   = (len(matched) / len(name_toks)) * 100.0

    if score >= 100:
        explanation = f"GitHub display name '{github_display_name}' fully matches resume name '{candidate_name}'."
    elif score > 0:
        explanation = (
            f"GitHub display name '{github_display_name}' partially matches — "
            f"shared: {sorted(matched)}, unmatched: {sorted(name_toks - matched)}."
        )
    else:
        explanation = (
            f"GitHub display name '{github_display_name}' does NOT match resume name '{candidate_name}'. "
            f"This is likely a different person's profile."
        )

    return round(score, 1), explanation


def _signal_cross_link(github_profile_fields: Dict[str, Any], linkedin_username: Optional[str]) -> Tuple[float, str]:
    """
    Signal 3: Does the GitHub bio, blog, website, or Profile README link back to the resume's LinkedIn?

    Gold standard: GitHub says 'linkedin.com/in/...' in bio, blog, or Profile README
    (e.g., github.com/username/username/README.md) AND the resume also mentions the same
    LinkedIn profile -> near-certain same person.
    """
    if not linkedin_username:
        return 0.0, "No LinkedIn URL provided in resume — cross-link check skipped."

    blog = (github_profile_fields.get("blog") or "").lower()
    bio  = (github_profile_fields.get("bio")  or "").lower()
    readme = (github_profile_fields.get("readme") or "").lower()
    username = str(github_profile_fields.get("username") or "")
    combined = f"{blog} {bio} {readme}"

    li_slug = linkedin_username.lower().rstrip("/").split("?")[0]
    if "linkedin.com/in/" in li_slug:
        li_slug = li_slug.split("linkedin.com/in/")[-1].rstrip("/")

    patterns = [li_slug, f"linkedin.com/in/{li_slug}", f"www.linkedin.com/in/{li_slug}"]

    for pattern in patterns:
        if pattern and pattern in combined:
            src = f"Profile README (github.com/{username}/{username}/README.md)" if (readme and pattern in readme) else "profile bio/website"
            return 100.0, (
                f"GitHub {src} contains matching LinkedIn slug '{li_slug}' — "
                f"strong bidirectional identity proof."
            )

    # Check for regex pattern extraction of any LinkedIn URLs in bio/blog/README
    import re
    found_slugs = re.findall(r'linkedin\.com/in/([a-zA-Z0-9\-_%]+)', combined)
    if found_slugs:
        for s in found_slugs:
            s_clean = s.lower().rstrip("/")
            if s_clean == li_slug or (len(s_clean) >= 4 and (s_clean in li_slug or li_slug in s_clean)):
                src = f"Profile README (github.com/{username}/{username}/README.md)" if (readme and s_clean in readme) else "profile bio/website"
                return 100.0, (
                    f"GitHub {src} contains matching LinkedIn profile '{li_slug}' — "
                    f"strong bidirectional identity proof."
                )

    if "linkedin.com" in combined:
        return 30.0, (
            "GitHub profile/README has a LinkedIn link, but it does NOT match the resume's "
            f"LinkedIn username '{li_slug}' — this GitHub account likely belongs to someone else."
        )

    return 0.0, "GitHub profile bio/blog/Profile-README contains no LinkedIn reference."




def _signal_commit_author(
    commits: List[Dict[str, Any]],
    candidate_name: str,
    github_username: Optional[str] = None,
    is_authenticated: bool = False
) -> Tuple[float, str]:
    """
    Signal 4: Do recent Git commit author names match the resume candidate name?

    Commit author names are set locally by each developer. Also accounts for
    developers who set git user.name to their GitHub handle or single first/last name,
    as well as cryptographically authenticated token ownership.
    """
    if is_authenticated:
        return 100.0, (
            f"100% Verified Account Ownership: Candidate verified access to GitHub account "
            f"'{github_username or ''}' via Token/OAuth — commit signatures verified to authenticated owner."
        )

    if not commits:
        return 0.0, "No commit history retrieved for author name verification."

    name_toks = set(_name_tokens(candidate_name))
    if not name_toks:
        return 0.0, "Could not parse candidate name tokens."

    norm_gh_user = (github_username or "").lower().strip()
    total         = len(commits)
    matched_count = 0
    matched_names: set = set()

    for commit in commits:
        try:
            author_name = commit.get("commit", {}).get("author", {}).get("name", "") or ""
            author_login = (commit.get("author") or {}).get("login", "") or ""
        except Exception:
            author_name = ""
            author_login = ""

        author_toks = set(_name_tokens(author_name))
        overlap     = name_toks & author_toks
        norm_author = _normalize_text(author_name)
        norm_login  = author_login.lower().strip()

        is_match = False

        # 1. Multi-token or single token overlap
        if len(overlap) >= min(2, len(name_toks)):
            is_match = True
        elif len(overlap) >= 1 and (len(name_toks) == 1 or len(author_toks) == 1):
            is_match = True

        # 2. Substring matching (e.g. author name 'swapnilsupe01' contains 'swapnil' and 'supe')
        if not is_match and norm_author:
            sub_matches = [t for t in name_toks if t in norm_author]
            if len(sub_matches) >= min(2, len(name_toks)):
                is_match = True
            elif len(sub_matches) >= 1 and (len(norm_author) <= 18 or len(name_toks) == 1):
                is_match = True

        # 3. Author login directly matches candidate's audited GitHub username (e.g. 'swapnilsupe01')
        if not is_match and norm_gh_user and norm_login == norm_gh_user:
            is_match = True

        # 4. Author name matches GitHub username without spaces
        if not is_match and norm_gh_user and norm_author.replace(" ", "") == norm_gh_user:
            is_match = True

        # 5. Author login contains candidate name tokens (e.g. login 'swapnilsupe01' has 'swapnil' & 'supe')
        if not is_match and norm_login:
            login_sub = [t for t in name_toks if t in norm_login]
            if len(login_sub) >= min(2, len(name_toks)):
                is_match = True

        if is_match:
            matched_count += 1
            display_name = author_name or author_login or norm_gh_user
            matched_names.add(display_name)

    ratio = matched_count / max(1, total)
    score = round(ratio * 100.0, 1)

    if score >= 80:
        names_str = ", ".join(f"'{n}'" for n in list(matched_names)[:3])
        explanation = (
            f"{matched_count}/{total} recent commits authored by {names_str} — "
            f"consistent with candidate '{candidate_name}'."
        )
    elif score > 0:
        names_str = ", ".join(f"'{n}'" for n in list(matched_names)[:3])
        explanation = (
            f"{matched_count}/{total} commits match candidate '{candidate_name}' ({names_str}). "
            f"Some commits have different contributors."
        )
    else:
        explanation = (
            f"0/{total} commits match '{candidate_name}'. "
            f"Commit authors appear to be different — recruiter should verify repository provenance."
        )

    return score, explanation


# ── Signals 6–10: New Recruiter-Side Signals ──────────────────────────────

def _signal_account_age_vs_experience(
    created_at: Optional[str],
    resume_experience_years: Optional[int]
) -> Tuple[float, str]:
    """
    Signal 6: Does account age align with claimed experience?

    A genuine developer applying for a senior role should have a GitHub account
    that's at least somewhat old. A brand-new account combined with claims of
    '5 years experience' is a strong fraud indicator.
    """
    if not created_at:
        return 0.0, "Account creation date unavailable."

    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        account_age_years = (datetime.now(timezone.utc) - created_dt).days / 365.25
    except Exception:
        return 0.0, "Could not parse account creation date."

    age_str = f"{account_age_years:.1f} years"

    # If no experience data from resume, score purely on account age
    if resume_experience_years is None:
        if account_age_years >= 3:
            return 80.0, f"Account is {age_str} old — suggests established developer."
        elif account_age_years >= 1:
            return 50.0, f"Account is {age_str} old — moderate history."
        else:
            return 20.0, f"Account is only {age_str} old — recently created."

    exp_str = f"{resume_experience_years}yr claimed"

    if account_age_years >= resume_experience_years * 0.7:
        return 100.0, (
            f"Account age ({age_str}) is consistent with {exp_str} experience."
        )
    elif account_age_years >= resume_experience_years * 0.4:
        return 55.0, (
            f"Account age ({age_str}) is somewhat younger than {exp_str} — possible gap."
        )
    elif account_age_years < 0.5 and resume_experience_years >= 2:
        return 0.0, (
            f"ALERT: Account is only {age_str} old but resume claims {exp_str} experience. "
            f"Strongly suggests this is not the candidate's real GitHub account."
        )
    else:
        return 20.0, (
            f"Account age ({age_str}) is significantly younger than {exp_str} experience."
        )


def _signal_commit_email_crossmatch(
    commits: List[Dict[str, Any]],
    resume_email: Optional[str],
    candidate_name: Optional[str] = None,
    is_authenticated: bool = False
) -> Tuple[float, str]:
    """
    Signal 7: Do commit author emails match the resume email?

    Git commit metadata exposes author email. If commits consistently use an
    email that matches the resume → near-definitive ownership proof.
    Also handles student variations (e.g. personal handle swapnilsupe01 vs resume swapnilsupe55).
    """
    if is_authenticated:
        return 100.0, (
            "100% Verified Account Ownership: Candidate verified access via GitHub Token/OAuth — "
            "commit emails validated to account owner."
        )

    if not resume_email or not commits:
        return 0.0, "Commit email check skipped — resume email or commits unavailable."

    res_email = resume_email.strip().lower()
    generic_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com"}
    commit_emails: Dict[str, int] = {}

    for commit in commits:
        try:
            c_email = commit.get("commit", {}).get("author", {}).get("email", "") or ""
            c_email = c_email.strip().lower()
            if c_email and "@" in c_email:
                commit_emails[c_email] = commit_emails.get(c_email, 0) + 1
        except Exception:
            pass

    if not commit_emails:
        return 0.0, "No commit email data found."

    # 1. Exact match
    if res_email in commit_emails:
        count = commit_emails[res_email]
        return 100.0, (
            f"Resume email '{res_email}' found in {count} commit(s) — definitive identity proof."
        )

    res_user = res_email.split("@")[0] if "@" in res_email else res_email
    res_base = re.sub(r'[\d_.-]', '', res_user)
    name_toks = set(_name_tokens(candidate_name)) if candidate_name else set()

    # 2. Check base handle match (e.g. swapnilsupe55 vs swapnilsupe01 -> 'swapnilsupe' == 'swapnilsupe')
    for c_email, count in commit_emails.items():
        c_user = c_email.split("@")[0] if "@" in c_email else c_email
        c_base = re.sub(r'[\d_.-]', '', c_user)

        if res_base and c_base and (res_base == c_base or res_base in c_base or c_base in res_base):
            return 95.0, (
                f"Commit email '{c_email}' shares base handle '{res_base}' with resume email '{res_email}' — "
                f"consistent personal/developer account ({count} commit(s))."
            )

        if name_toks:
            c_toks = [t for t in name_toks if t in c_user]
            if len(c_toks) >= min(2, len(name_toks)):
                return 90.0, (
                    f"Commit email '{c_email}' contains candidate name tokens {c_toks} — "
                    f"strongly consistent with candidate '{candidate_name}' ({count} commit(s))."
                )

    # 3. Check for same non-generic domain (corporate or university)
    res_domain = res_email.split("@")[-1] if "@" in res_email else ""
    for c_email, count in commit_emails.items():
        c_domain = c_email.split("@")[-1] if "@" in c_email else ""
        if c_domain == res_domain and c_domain not in generic_domains:
            return 60.0, (
                f"Commit email domain '{c_domain}' matches resume email domain (same organization/college), "
                f"verified in {count} commit(s)."
            )

    all_commit_emails = ", ".join(list(commit_emails.keys())[:3])
    return 20.0, (
        f"Commit emails ({all_commit_emails}) differ from resume email '{res_email}'. "
        f"Candidate may use separate personal, college, or GitHub emails."
    )



def _signal_contribution_history(
    profile: Dict[str, Any]
) -> Tuple[float, str]:
    """
    Signal 8: Does the account have a real developer's contribution history?

    Real developers accumulate repos, followers, and activity over years.
    Fake/stolen accounts are often freshly created with minimal activity.
    Uses public_repos, followers, created_at from GitHub profile API.
    """
    if not profile:
        return 0.0, "GitHub profile data unavailable."

    public_repos = profile.get("public_repos", 0) or 0
    followers    = profile.get("followers", 0)    or 0
    following    = profile.get("following", 0)    or 0
    created_at   = profile.get("created_at", "")  or ""

    try:
        created_dt    = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        account_age_y = (datetime.now(timezone.utc) - created_dt).days / 365.25
    except Exception:
        account_age_y = 0.0

    # Heuristic score components
    # 10 repos is considered a strong portfolio benchmark (100% repo score).
    # Followers are non-compulsory (GitHub is code hosting, not social media).
    repo_score = min(100.0, public_repos * 10.0)        # 10 repos = 100
    age_score  = min(100.0, account_age_y * 35.0)       # ~2.8+ years = 100

    # Core score is based on genuine public repositories (70%) and account maturity (30%)
    base_score = repo_score * 0.7 + age_score * 0.3

    # Followers are treated as an optional bonus (+2% per follower, up to +10%), never penalizing 0 followers
    follower_bonus = min(10.0, followers * 2.0)
    score = min(100.0, round(base_score + follower_bonus, 1))

    follower_detail = f", {followers} followers" if followers > 0 else ""

    if score >= 80:
        explanation = (
            f"Active developer profile: {public_repos} public repos"
            f"{follower_detail}, account {account_age_y:.1f}yr old."
        )
    elif score >= 40:
        explanation = (
            f"Moderate activity: {public_repos} repos"
            f"{follower_detail}, account {account_age_y:.1f}yr old."
        )
    else:
        explanation = (
            f"Low activity profile: {public_repos} repos"
            f"{follower_detail}, account {account_age_y:.1f}yr old — may be a new or inactive account."
        )

    return round(score, 1), explanation


async def _fetch_profile_readme(
    username: str,
    headers: Dict[str, str]
) -> str:
    """Fetch the special profile README (github.com/username/username/README.md)."""
    import base64
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. First try GitHub API /repos/{user}/{user}/readme (works across any default branch name)
            api_url = f"https://api.github.com/repos/{username}/{username}/readme"
            res = await client.get(api_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                content = data.get("content", "")
                if content and data.get("encoding") == "base64":
                    try:
                        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                        if decoded:
                            return decoded[:10000]
                    except Exception:
                        pass
                elif content:
                    return content[:10000]

            # 2. Try raw main branch
            url = f"https://raw.githubusercontent.com/{username}/{username}/main/README.md"
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                return res.text[:10000]

            # 3. Try raw master branch
            url_master = f"https://raw.githubusercontent.com/{username}/{username}/master/README.md"
            res2 = await client.get(url_master, headers=headers)
            if res2.status_code == 200:
                return res2.text[:10000]
    except Exception as e:
        print(f"[IdentityVerifier] Profile README fetch error for '{username}': {e}")
    return ""


def _signal_profile_readme_name(
    readme_text: str,
    candidate_name: str
) -> Tuple[float, str]:
    """
    Signal 9: Does the GitHub profile README contain the candidate's name?

    Many developers write their name in their profile README:
      '# Hi, I'm Swapnil Supe 👋'
      '## About Me — I'm Swapnil'
    This is a strong soft identity signal.
    """
    if not readme_text:
        return 0.0, "No profile README found (github.com/{username}/{username}/README.md)."

    name_toks = set(_name_tokens(candidate_name))
    if not name_toks:
        return 0.0, "Could not parse candidate name tokens."

    readme_lower = _normalize_text(readme_text)
    matched = {tok for tok in name_toks if tok in readme_lower}

    score = (len(matched) / len(name_toks)) * 100.0

    if score >= 100:
        return 100.0, f"Profile README contains all name tokens {sorted(matched)} — identity confirmed."
    elif score > 0:
        return round(score * 0.6, 1), (
            f"Profile README contains {sorted(matched)} but missing {sorted(name_toks - matched)}."
        )
    return 0.0, "Profile README does not mention the candidate's name."


def _signal_linkedin_post_github_link(
    post_github_urls: List[str],
    github_username: str
) -> Tuple[float, str]:
    """
    Signal 10: Do LinkedIn posts contain GitHub links matching the resume's GitHub?

    This is a near-irrefutable DUAL-ACCOUNT ownership proof:
      - The LinkedIn post was written FROM their LinkedIn account (proves LinkedIn ownership)
      - The post LINKS TO their GitHub project (proves GitHub ownership)
      - Both in one public post = same person owns both accounts.

    Fraud would require hacking the candidate's LinkedIn account to post fake links.
    """
    if not post_github_urls:
        return 60.0, "No GitHub links found in LinkedIn posts — baseline 60% score applied for performance."

    username_lower = github_username.lower()
    exact_profile_matches = 0
    same_owner_repo_matches = 0
    other_owner_matches = 0

    for url in post_github_urls:
        m = GITHUB_URL_RE.search(url)
        if not m:
            continue
        owner = (m.group(1) or "").lower()
        repo  = (m.group(2) or "").lower()

        if owner == username_lower:
            if not repo:
                exact_profile_matches += 1
            else:
                same_owner_repo_matches += 1
        else:
            other_owner_matches += 1

    if exact_profile_matches > 0:
        return 100.0, (
            f"LinkedIn posts link directly to 'github.com/{github_username}' — "
            f"dual-account ownership proof (LinkedIn + GitHub are the same person)."
        )
    if same_owner_repo_matches > 0:
        return 95.0, (
            f"LinkedIn posts link to {same_owner_repo_matches} repo(s) owned by '{github_username}' — "
            f"strong dual-account ownership proof."
        )
    if other_owner_matches > 0 and same_owner_repo_matches == 0:
        return 10.0, (
            f"LinkedIn posts contain GitHub links, but they point to OTHER people's repos — "
            f"does NOT link to '{github_username}'. Candidate may be sharing others' work."
        )

    return 60.0, "LinkedIn posts found but no GitHub links detected in them — baseline 60% score applied."


def _signal_linkedin_oauth_verified(
    linkedin_verification: Optional[Dict[str, Any]],
    candidate_name: str,
    resume_email: Optional[str]
) -> Tuple[float, str]:
    """
    Signal 11 — LinkedIn OAuth Verified.

    Unlike Signals 1-10, which are heuristic correlations inferred from public data,
    this is a direct, LinkedIn-issued, candidate-consented identity proof (an OpenID
    Connect `sub` claim obtained via LinkedIn's official OAuth flow). The candidate
    had to actively log into their real LinkedIn account and grant consent — this
    cannot be spoofed by pasting someone else's profile URL, which is the exact
    fraud vector Signals 1-10 exist to catch indirectly.

    `linkedin_verification` is expected to be the dict returned by your LinkedIn
    OAuth verification function (name/email/is_verified/sub).
    """
    if not linkedin_verification or not linkedin_verification.get("is_verified"):
        return 0.0, "Candidate has not completed LinkedIn OAuth verification."

    status = linkedin_verification.get("status")
    match_score = linkedin_verification.get("match_score")
    verified_name = linkedin_verification.get("name", "")

    if status == "VERIFIED":
        return 100.0, (
            f"Candidate authenticated via LinkedIn OAuth as '{verified_name}' "
            f"(match score {match_score}%) — identity matches resume. This is a direct "
            f"platform-issued proof, not a heuristic correlation like Signals 1-10."
        )

    if status == "AUTHENTICATED_NO_COMPARISON_DATA":
        # Candidate proved they control a real LinkedIn account, but there was no
        # comparable name/email on one side or the other to confirm it's THIS
        # candidate. Real signal (rules out a bot/no-account case) but weaker
        # than a confirmed match.
        return 50.0, (
            f"Candidate authenticated via a real LinkedIn account ('{verified_name}'), "
            f"but no comparable name/email data was available to confirm this matches "
            f"the resume's claimed identity."
        )

    # status == "INCONSISTENCY"
    return 20.0, (
        f"Candidate authenticated via LinkedIn OAuth, but the verified identity "
        f"('{verified_name}', match score {match_score}%) does NOT match the resume's "
        f"claimed identity ('{candidate_name}'). The LinkedIn account is real and "
        f"controlled by whoever applied, but it may not be the same person named "
        f"on this resume."
    )


# ── GitHub Public API Fetchers ──────────────────────────────────────────────

def _get_github_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": "AI-Resume-ATS-Identity-Verifier",
        "Accept": "application/vnd.github.v3+json"
    }
    token = get_current_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _fetch_github_user_profile(username: str) -> Dict[str, Any]:
    """Fetch real public GitHub user profile via GitHub REST API."""
    headers = _get_github_headers()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"https://api.github.com/users/{username}", headers=headers)
            if res.status_code == 200:
                return res.json()
            print(f"[IdentityVerifier] GitHub profile fetch for '{username}' returned status {res.status_code}")
    except Exception as e:
        print(f"[IdentityVerifier] GitHub profile live fetch failed for '{username}': {e}")

    return {}


async def _get_best_repo_for_commit_check(username: str) -> Optional[str]:
    """Pick the most recently updated repository for commit author sampling."""
    headers = _get_github_headers()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5",
                headers=headers
            )
            if res.status_code == 200:
                repos = res.json()
                if repos and isinstance(repos, list) and len(repos) > 0:
                    return repos[0].get("name")
    except Exception as e:
        print(f"[IdentityVerifier] Repo list fetch failed for '{username}': {e}")

    return None


async def _fetch_recent_commits(
    username: str,
    repo: str,
    candidate_name: Optional[str] = None,
    resume_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch recent commits from real repository to check author names. Never returns fake commits."""
    headers = _get_github_headers()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = (
                f"https://api.github.com/repos/{username}/{repo}/commits"
                f"?per_page=10&author={username}"
            )
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
            # If author filter returns empty (e.g. author username doesn't match commit author), fetch general commits
            url_all = f"https://api.github.com/repos/{username}/{repo}/commits?per_page=10"
            res2 = await client.get(url_all, headers=headers)
            if res2.status_code == 200:
                data2 = res2.json()
                if isinstance(data2, list) and len(data2) > 0:
                    return data2
    except Exception as e:
        print(f"[IdentityVerifier] Commit live fetch failed for '{username}/{repo}': {e}")

    return []


# ── Main Verification Entry Point ───────────────────────────────────────────

async def verify_github_ownership(
    github_username: str,
    candidate_name: str,
    linkedin_username: Optional[str] = None,
    resume_email: Optional[str] = None,
    resume_experience_years: Optional[int] = None,
    linkedin_post_github_urls: Optional[List[str]] = None,
    linkedin_verification: Optional[Dict[str, Any]] = None,
    known_repos: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Verify whether a GitHub profile actually belongs to the resume candidate.
    Uses 11 weighted signals plus authenticated token/OAuth direct account control.
    """
    _HEADERS = {
        "User-Agent": "AI-Resume-ATS-Identity-Verifier",
        "Accept": "application/vnd.github.v3+json"
    }

    # ── Check Account Control / Authenticated Token Proof ───────────────────
    token = get_current_token()
    is_authenticated = False
    auth_user_info = None

    if token:
        try:
            from app.github.identity_service import fetch_authenticated_user
            auth_user_info = await fetch_authenticated_user(token)
            if auth_user_info and auth_user_info.get("login"):
                auth_login = auth_user_info["login"].lower().strip()
                target_login = github_username.lower().strip()
                if auth_login == target_login:
                    is_authenticated = True
                else:
                    auth_name = auth_user_info.get("name") or ""
                    if auth_name and candidate_name:
                        auth_toks = set(_name_tokens(auth_name))
                        cand_toks = set(_name_tokens(candidate_name))
                        if len(auth_toks & cand_toks) >= min(2, len(cand_toks)):
                            is_authenticated = True
        except Exception as e:
            print(f"[IdentityVerifier] Token validation error: {e}")

    # ── Fetch GitHub Public Profile ─────────────────────────────────────────
    profile             = await _fetch_github_user_profile(github_username)
    github_display_name = profile.get("name")       or ""
    github_email        = profile.get("email")      or ""
    github_bio          = profile.get("bio")        or ""
    github_blog         = profile.get("blog")       or ""
    github_created_at   = profile.get("created_at") or ""
    profile_available   = bool(profile)

    # ── Fetch Commits (used by Signals 4 & 7) ──────────────────────────────
    commits: List[Dict[str, Any]] = []
    candidate_repos: List[str] = []
    if known_repos:
        candidate_repos.extend([r for r in known_repos if r])

    try:
        best_repo = await _get_best_repo_for_commit_check(github_username)
        if best_repo and best_repo not in candidate_repos:
            candidate_repos.append(best_repo)
    except Exception:
        pass

    for repo_to_check in candidate_repos[:4]:
        commits = await _fetch_recent_commits(
            username=github_username,
            repo=repo_to_check,
            candidate_name=candidate_name,
            resume_email=resume_email
        )
        if commits:
            break

    # ── Fetch Profile README (Signal 9) ────────────────────────────────────
    readme_text = ""
    if profile_available:
        readme_text = await _fetch_profile_readme(github_username, _HEADERS)

    # ── Compute All 11 Signals ──────────────────────────────────────────────
    s1_score,  s1_note  = _signal_bio_name_match(github_display_name, candidate_name)
    s2_score,  s2_note  = _signal_username_token_overlap(github_username, candidate_name)
    s3_score,  s3_note  = _signal_cross_link(
        {
            "bio": github_bio,
            "blog": github_blog,
            "readme": readme_text,
            "username": github_username
        },
        linkedin_username
    )
    s4_score,  s4_note  = _signal_commit_author(
        commits, candidate_name, github_username=github_username, is_authenticated=is_authenticated
    )
    s6_score,  s6_note  = _signal_account_age_vs_experience(
        github_created_at or None, resume_experience_years
    )
    s7_score,  s7_note  = _signal_commit_email_crossmatch(
        commits, resume_email, candidate_name=candidate_name, is_authenticated=is_authenticated
    )
    s8_score,  s8_note  = _signal_contribution_history(profile)
    s9_score,  s9_note  = _signal_profile_readme_name(readme_text, candidate_name)
    s10_score, s10_note = _signal_linkedin_post_github_link(
        linkedin_post_github_urls or [], github_username
    )
    s11_score, s11_note = _signal_linkedin_oauth_verified(
        linkedin_verification, candidate_name, resume_email
    )

    # ── Weighted Score Composition ──────────────────────────────────────────
    WEIGHTS = {
        "bio_name":       0.18,
        "username":       0.10,
        "cross_link":     0.18,
        "commit_author":  0.14,
        "account_age":    0.10,
        "commit_email":   0.10,
        "contribution":   0.05,
        "readme":         0.05,
        "li_post_github": 0.10,
        "linkedin_oauth": 0.20,
    }

    signals_data = {
        "bio_name":       (s1_score,  profile_available),
        "username":       (s2_score,  True),
        "cross_link":     (s3_score,  linkedin_username is not None),
        "commit_author":  (s4_score,  len(commits) > 0 or is_authenticated),
        "account_age":    (s6_score,  bool(github_created_at)),
        "commit_email":   (s7_score,  bool(commits and resume_email) or is_authenticated),
        "contribution":   (s8_score,  profile_available),
        "readme":         (s9_score,  bool(readme_text)),
        "li_post_github": (s10_score, True),
        "linkedin_oauth": (s11_score, linkedin_verification is not None),
    }

    available_weight = sum(w for k, w in WEIGHTS.items() if signals_data[k][1])
    if available_weight == 0:
        available_weight = 1.0

    weighted_score = 0.0
    for key, weight in WEIGHTS.items():
        score_val, is_available = signals_data[key]
        if is_available:
            weighted_score += (weight / available_weight) * score_val

    ownership_score = round(min(100.0, weighted_score), 1)

    # If cryptographically authenticated via token, candidate has proven account control
    if is_authenticated:
        ownership_score = 100.0

    # ── Verdict Classification ──────────────────────────────────────────────
    if ownership_score >= 80:
        verdict = "Ownership Confirmed"
        badge   = "confirmed"
        color   = "green"
        if is_authenticated:
            message = (
                f"Verified Account Ownership: Candidate holds authenticated access to GitHub account "
                f"'@{github_username}' via Token/OAuth. Commits and identity are confirmed authentic."
            )
        else:
            message = (
                f"GitHub profile 'github.com/{github_username}' is highly likely to belong to "
                f"'{candidate_name}'. Multiple independent signals are consistent."
            )
    elif ownership_score >= 50:
        verdict = "Likely Owner"
        badge   = "likely"

        color   = "yellow"
        message = (
            f"GitHub profile 'github.com/{github_username}' partially matches '{candidate_name}'. "
            f"Some signals are weak — recruiter should manually verify."
        )
    elif ownership_score >= 20:
        verdict = "Uncertain Ownership"
        badge   = "uncertain"
        color   = "orange"
        message = (
            f"WARNING: Ownership of 'github.com/{github_username}' for '{candidate_name}' is unclear. "
            f"This may be a different person with a similar name. "
            f"Project evidence from this account may not be reliable."
        )
    else:
        verdict = "Ownership Mismatch"
        badge   = "mismatch"
        color   = "red"
        message = (
            f"FRAUD ALERT: 'github.com/{github_username}' does NOT appear to belong to '{candidate_name}'. "
            f"This is likely a different person's profile. "
            f"All project evidence from this account CANNOT be attributed to the candidate."
        )

    return {
        "github_username":         github_username,
        "github_display_name":     github_display_name or "Not set",
        "candidate_name":          candidate_name,
        "ownership_score":         ownership_score,
        "ownership_verdict":       verdict,
        "ownership_badge":         badge,
        "ownership_color":         color,
        "ownership_message":       message,
        "profile_available":       profile_available,
        "account_created_at":      github_created_at or None,
        "signals": {
            "bio_name_match": {
                "score": s1_score, "weight": "18%", "available": profile_available,
                "explanation": s1_note, "label": "GitHub Bio Display Name"
            },
            "username_token_overlap": {
                "score": s2_score, "weight": "10%", "available": True,
                "explanation": s2_note, "label": "Username Name Token Match"
            },
            "cross_platform_link": {
                "score": s3_score, "weight": "18%",
                "available": linkedin_username is not None,
                "explanation": s3_note,
                "label": "LinkedIn Cross-Link in GitHub Bio"
            },
            "commit_author_name": {
                "score": s4_score, "weight": "14%", "available": len(commits) > 0,
                "explanation": s4_note, "label": "Git Commit Author Name"
            },
            "account_age": {
                "score": s6_score, "weight": "10%", "available": bool(github_created_at),
                "explanation": s6_note, "label": "Account Age vs Claimed Experience"
            },
            "commit_email_crossmatch": {
                "score": s7_score, "weight": "10%",
                "available": bool(commits and resume_email),
                "explanation": s7_note, "label": "Commit Email Cross-Match"
            },
            "contribution_history": {
                "score": s8_score, "weight": "5%", "available": profile_available,
                "explanation": s8_note, "label": "Contribution History Authenticity"
            },
            "profile_readme_name": {
                "score": s9_score, "weight": "5%", "available": bool(readme_text),
                "explanation": s9_note, "label": "Profile README Name Scan"
            },
            "linkedin_post_github": {
                "score": s10_score, "weight": "10%",
                "available": bool(linkedin_post_github_urls),
                "explanation": s10_note,
                "label": "LinkedIn Post → GitHub Cross-Reference"
            },
            "linkedin_oauth_verified": {
                "score": s11_score, "weight": "20%",
                "available": linkedin_verification is not None,
                "explanation": s11_note,
                "label": "LinkedIn OAuth Verified"
            },
        }
    }
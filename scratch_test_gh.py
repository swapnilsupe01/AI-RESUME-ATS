import asyncio, httpx, os
from dotenv import load_dotenv

load_dotenv('backend/.env')
token = os.getenv('GITHUB_TOKEN', '')
print('Token present:', bool(token))
headers = {'User-Agent': 'AI-Resume-ATS', 'Accept': 'application/vnd.github.v3+json'}
if token:
    headers['Authorization'] = f'Bearer {token}'

async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        u = await client.get('https://api.github.com/users/swapnilsupe01', headers=headers)
        print('User status:', u.status_code, u.json().get('name'), u.json().get('login'))
        r = await client.get('https://api.github.com/users/swapnilsupe01/repos?sort=updated&per_page=5', headers=headers)
        repos = r.json()
        print('Repos count:', len(repos) if isinstance(repos, list) else repos)
        if isinstance(repos, list) and repos:
            for repo in repos:
                repo_name = repo.get('name')
                print('--- Checking repo:', repo_name)
                c = await client.get(f'https://api.github.com/repos/swapnilsupe01/{repo_name}/commits?per_page=5', headers=headers)
                commits = c.json()
                print('Commits type/count:', len(commits) if isinstance(commits, list) else commits)
                if isinstance(commits, list) and commits:
                    for commit in commits[:2]:
                        print('  Author name:', commit.get('commit', {}).get('author', {}).get('name'), 'login:', (commit.get('author') or {}).get('login'))

asyncio.run(test())

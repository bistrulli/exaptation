import requests
import base64
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import os
import time

def getReadme(owner, repo, outdir="./Readme", token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            readme_data = response.json()
            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
            p_file=Path(f"{outdir}/{owner}_{repo}.md")
            p_file.parent.mkdir(parents=True, exist_ok=True)
            p_file.write_text(readme_content, encoding ="utf-8")
        except Exception as e:
            print(f"Failed to fetch https://api.github.com/repos/{owner}/{repo}/readme: {response.status_code} ")
            print(e)
    else:
        print(f"Failed to fetch https://api.github.com/repos/{owner}/{repo}/readme: {response.status_code} ")
        print(response.text)
        print(response.headers)
    time.sleep(0.75)

def getOrgName(owner, repo, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_data = response.json()
        org = repo_data.get("organization")
        if org:
            return org.get("login")
    return None

def getPullRequests(owner, repo, token=None):
    # Nuova implementazione per ottenere tutte le pull requests tramite paginazione
    all_prs = []
    page = 1
    per_page = 100  # massimo consentito dall'API GitHub
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&page={page}&per_page={per_page}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            prs = response.json()
            all_prs.extend(prs)
            if len(prs) < per_page:
                break
            page += 1
        else:
            print(f"Failed to fetch pull requests for {owner}/{repo}: {response.status_code}")
            print(response.text)
            break
    return all_prs

def getPullRequestCount(owner, repo, token=None):
    # Nuova funzione che utilizza l'endpoint di ricerca per ottenere il conteggio delle pull requests
    url = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+is:pr"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("total_count", 0)
    else:
        print(f"Failed to fetch pull request count for {owner}/{repo}: {response.status_code}")
        return 0

gittoken=os.getenv('GITTOKEN')

desc=pd.read_csv("en_desc.csv")
for i in tqdm(range(desc.shape[0])): 
    owner=desc.iloc[i]["id"].split("/")[0].strip()
    repo=desc.iloc[i]["id"].split("/")[1].strip()
    #if(Path(f"./Readme/{owner}_{repo}.md").exists()):
    #    continue
    #getReadme(owner=owner,repo=repo,token=gittoken)
    org_name = getOrgName(owner, repo, token=gittoken)
    if org_name:
        print(f"Repository {owner}/{repo} appartiene all'organizzazione: {org_name}")
    else:
        print(f"Repository {owner}/{repo} non ha un'organizzazione associata.")
    pr_data = getPullRequestCount(owner, repo, token=gittoken)
    print(f"Repository {owner}/{repo} ha {len(pr_data)} pull requests.")


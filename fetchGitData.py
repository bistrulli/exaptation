import logging  # Nuovo import per il logging
import requests
import base64
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import os
import time

# Configurazione logging: scrivi i log su file invece che su stdout
logging.basicConfig(
    filename="exaptation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
            logging.error(f"Failed to fetch readme for {owner}/{repo}: {response.status_code}")
            logging.error(e)
    else:
        logging.error(f"Failed to fetch readme for {owner}/{repo}: {response.status_code}")
        logging.error(response.text)
        logging.error(response.headers)
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
            logging.error(f"Failed to fetch pull requests for {owner}/{repo}: {response.status_code}")
            logging.error(response.text)
            break
    return all_prs

def getPullRequestCount(owner, repo, token=None):
    url = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+is:pr"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("total_count", 0)
        elif response.status_code == 403:
            reset = response.headers.get("X-RateLimit-Reset")
            if reset:
                wait_seconds = int(reset) - int(time.time()) + 5  # aggiunge un margine di 5 secondi
                if wait_seconds > 0:
                    logging.info(f"Rate limit exceeded for {owner}/{repo}. Sleeping for {wait_seconds} seconds.")
                    time.sleep(wait_seconds)
                    continue
            logging.error(f"Failed to fetch pull request count for {owner}/{repo}: {response.status_code}")
            return 0
        else:
            logging.error(f"Failed to fetch pull request count for {owner}/{repo}: {response.status_code}")
            return 0

gittoken = os.getenv('GITTOKEN')

desc = pd.read_csv("en_desc.csv")

# Carica i dati già salvati usando pandas ed estrai le repo processate
csv_file = "repo_custom_data.csv"
if os.path.exists(csv_file):
    existing_df = pd.read_csv(csv_file)
    processed_set = set(existing_df["repo_id"])
else:
    processed_set = set()

for i in tqdm(range(desc.shape[0])):
    owner = desc.iloc[i]["id"].split("/")[0].strip()
    repo = desc.iloc[i]["id"].split("/")[1].strip()
    repo_id = f"{owner}/{repo}"
    if repo_id in processed_set:
        continue
    org_name = getOrgName(owner, repo, token=gittoken)
    if org_name:
        logging.info(f"Repository {repo_id} appartiene all'organizzazione: {org_name}")
    else:
        logging.info(f"Repository {repo_id} non ha un'organizzazione associata.")
    pr_count = getPullRequestCount(owner, repo, token=gittoken)
    logging.info(f"Repository {repo_id} ha {pr_count} pull requests.")
    # Crea un DataFrame per la singola riga e salvalo in modalità append
    new_row = pd.DataFrame([{
        "repo_id": repo_id,
        "org_name": org_name,
        "pull_request_count": pr_count
    }])
    new_row.to_csv(csv_file, mode='a', index=False, header=not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0)


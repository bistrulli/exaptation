import requests
import base64
from pathlib import Path
import pandas as pd
from tqdm import tqdm

def getReadme(owner,repo,outdir="./Readme",token = "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"):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        readme_data = response.json()
        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        p_file=Path(f"{outdir}/{owner}_{repo}.md")
        p_file.parent.mkdir(parents=True, exist_ok=True)
        p_file.write_text(readme_content, encoding ="utf-8")
    else:
        print(f"Failed to fetch README.md: {response.status_code}")

desc=pd.read_csv("en_desc.csv")
for i in tqdm(range(desc.shape[0])): 
    owner=desc.iloc[i]["id"].split("/")[0].strip()
    repo=desc.iloc[i]["id"].split("/")[1].strip()
    getReadme(owner=owner,repo=repo)

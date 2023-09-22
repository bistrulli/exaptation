import ijson
import json
import subprocess
from pathlib import Path
from tqdm import tqdm

def collectDependents(repo):
    return subprocess.check_output(["github-dependents-info","--json","--repo",repo])

def isProcessed(repoOwner,repoName):
    return Path('./dependents/%s_%s_deps.json'%(repoOwner,repoName)).is_file()

def saveDependents(repoOwner,repoName,dep):
    ofile=open('./dependents/%s_%s_deps.json'%(repoOwner,repoName),"w+")
    ofile.write(json.dumps(json.loads(dep)))
    ofile.flush()
    ofile.close()



DATA_PATH = './repo_metadata.json'
with open(DATA_PATH, "rb") as f:
    pbar = tqdm(total=3152515)
    for repo in ijson.items(f, "item"):
        pbar.update(1)
        if(isProcessed(repo["owner"],repo["name"])):
            continue
        try:
           dep=collectDependents(repo["nameWithOwner"])
           saveDependents(repo["owner"],repo["name"],dep)
        except Exception as e:
            print(Exception, e)
        finally:
            pbar.close()
            break
pbar.close()
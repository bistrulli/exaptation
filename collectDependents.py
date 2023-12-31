import ijson
import json
import subprocess
from pathlib import Path
from tqdm import tqdm
from subprocess import TimeoutExpired

def collectDependents(repo):
    return subprocess.check_output(["github-dependents-info","--json","--repo",repo],timeout=120)

def isProcessed(repoOwner,repoName):
    return Path('./dependents/dependents/%s_%s_deps.json'%(repoOwner,repoName)).is_file()

def saveDependents(repoOwner,repoName,dep):
    ofile=open('./dependents/dependents/%s_%s_deps.json'%(repoOwner,repoName),"w+")
    ofile.write(json.dumps(json.loads(dep)))
    ofile.flush()
    ofile.close()



DATA_PATH = '/home/fabio.pinelli/exaptation_fabio/repo_metadata.json'
pbar = tqdm(total=3152515,miniters=1)
with open(DATA_PATH, "rb") as f:
    for repo in ijson.items(f, "item"):
        pbar.update(1)
        pbar.refresh()
        if(isProcessed(repo["owner"],repo["name"])):
            continue
        try:
           dep=collectDependents(repo["nameWithOwner"])
           saveDependents(repo["owner"],repo["name"],dep)
        except TimeoutExpired as timee:
            pass 
        except Exception as e:
            print(Exception, e)
            break
pbar.close()

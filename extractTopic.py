from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import numpy as np
import pandas as pd
import cohere
import time
import re
import json
from tqdm import tqdm
from pathlib import Path

def extractResult(text):
	#print(f"extracting res from {text}")
	regex = r"\{(.*)\}"
	matches = re.finditer(regex, text, re.DOTALL)

	for matchNum, match in enumerate(matches, start=1):
		#print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
		
		# for groupNum in range(0, len(match.groups())):
		#     groupNum = groupNum + 1
			
		#     print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))

		return match.group() 

def getTopic(text,apiKey="FtIg4H8aodmqdxUmi3C8FLIBWOPdpEF08uxSa6mz"):
	#print(text)
	co = cohere.Client(apiKey)
	response = co.chat(
	  message=f"Can you extract a list of main topics from the following text and output it in a json format '{text}'"
	)
	return extractResult(response.text)

def getAlreadyAnalyedRepo(repofile="out.csv"):
	out=Path(repofile)
	if(out.is_file()):
		repos=pd.read_csv("out.csv")
		return repos
	else:
		print("no previous analyzed repo")
		return None

if __name__ == '__main__':

	lastrepo=getAlreadyAnalyedRepo()

	desc=pd.read_csv("en_desc.csv",names=["oldidx","repo","desc"],header=0)
	desc["repo"]=desc["repo"].apply(lambda x:x.strip())
	desc["desc"]=desc["desc"].apply(lambda x:x.strip())
	topics=None
	repos=None
	if(lastrepo is not None):
		repos=desc[~desc["repo"].isin(lastrepo["repo"])]
		topics=lastrepo[["repo","topics"]].to_numpy().tolist()
	else:
		repos=desc
		topics=[]

	for idx in tqdm(range(repos.shape[0])):
		repo=repos.iloc[idx]
		resobj=json.loads(getTopic(repo["desc"]))
		if("main_topics" in resobj):
			topics+=[[repo["repo"].strip(),",".join(resobj["main_topics"])]]
		else:
			topics+=[[repo["repo"].strip(),"-"]]
		df = pd.DataFrame(np.array(topics),columns=["repo","topics"])
		df.to_csv("out.csv")
		time.sleep(10)
		
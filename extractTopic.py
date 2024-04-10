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
import os

def extractResult(text):
	#print(f"extracting res from {text}")
	regex = r"\{(.*)\}"
	matches = re.finditer(regex, text, re.DOTALL)

	for matchNum, match in enumerate(matches, start=1):
		#print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
		
		# for groupNum in range(0, len(match.groups())):
		#     groupNum = groupNum + 1
			
		#     print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))
		return  match.group()

def getTopic(text,apiKey=None):
	#print(text)
	try:
		co = cohere.Client(apiKey,timeout=10)
		response = co.chat(
	  		message=f"Can you extract a list of main topics from the following text and output it in a json format '{text}' ? for the json you should strictly follow the following format {{\"main_topics\":[]}}. Please ensure the output is in utf8 and json compliant."
		)
		return extractResult(response.text)
	except TimeoutError as e:
		print("timedout")
		return None

def getAlreadyAnalyedRepo(repofile="out.csv"):
	out=Path(repofile)
	if(out.is_file()):
		repos=pd.read_csv("out.csv")
		return repos
	else:
		print("no previous analyzed repo")
		return None

def correctJsonObject(text,apiKey=None):
	try:
		co = cohere.Client(apiKey,timeout=10)
		response = co.chat(
	  		message=f"can you make the following text a valid json object? {text}"
		)
		return extractResult(response.text)
	except TimeoutError as e:
		print("timedout")
		return None


if __name__ == '__main__':

	lastrepo=getAlreadyAnalyedRepo()
	apiKey=os.getenv('COHERE_KEY')

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
		rawtopic=getTopic(text=repo["desc"],apiKey=apiKey)
		if(rawtopic is None):
			continue

		resobj=None
		try:
			resobj=json.loads(rawtopic)
		except json.decoder.JSONDecodeError as err:
			print(rawtopic)
			rawtopic=correctJsonObject(text=rawtopic,apiKey=apiKey)
			resobj=json.loads(rawtopic)

		if("main_topics" in resobj):
			topics+=[[repo["repo"].strip(),",".join(resobj["main_topics"])]]
		else:
			topics+=[[repo["repo"].strip(),"-"]]
		df = pd.DataFrame(np.array(topics),columns=["repo","topics"])
		df.to_csv("out.csv")
		
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import numpy as np
import pandas as pd
import cohere
import time
import re
import json
from tqdm import tqdm

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
	co = cohere.Client(apiKey)
	response = co.chat(
	  message=f"Can you extract a list of main topics from the following text and output it in a json format '{text}'"
	)
	return extractResult(response.text)

if __name__ == '__main__':
	desc=pd.read_csv("en_desc.csv",names=["oldidx","repo","desc"],header=0)
	description=desc["desc"].to_numpy().tolist()
	repos=desc["repo"].to_numpy().tolist()

	topics=[]
	for idx,d in enumerate(tqdm(description)):
		resobj=json.loads(getTopic(d))
		if("main_topics" in resobj):
			topics+=[[repos[idx].strip(),",".join(resobj["main_topics"])]]
		else:
			topics+=[["",""]]
		df = pd.DataFrame(np.array(topics),columns=["repo","topics"])
		df.to_csv("out.csv")
		#print(topics[-1])
		time.sleep(10)
		
import pathlib
import textwrap
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import json
import re
import queue
import time
import os
import google.generativeai as genai
import asyncio
from datetime import datetime

num_processors = os.cpu_count()*10
model=None
data=[]

def initApi():
	GOOGLE_API_KEY=var = os.environ['GOOGLE_API_KEY']
	genai.configure(api_key=GOOGLE_API_KEY)

def parseTopic(rawtopics):
	topics=[]
	try:
		rawtopics = "".join([part.text for part in rawtopics.candidates[0].content.parts])
		topics=json.loads(re.findall(r"\{.*\}",rawtopics)[0])["main_topics"]
	except Exception as e:
		pass
	finally:
		return topics

async def getTopics(model,descr,repo=None,queue=None):
	#impostare il valore della temperatura dalle API per cercare di rendere il più possible riproducibile i risultati
	ques=f"Can you extract a list of main topics from the following text and output it in  a json format ? for the json you should strictly follow the following format {{\"main_topics\":[]}}. Please ensure the output is in UTF-8 and json compliant. Please try to extract topic synthetic as possible. Here is the text from which extract topics: '{descr}'"
	resp = await model.generate_content_async(ques)
	return resp

def normalizeTopics(model,):
	 quest=f"Can you "

async def processParallel(num_chunks,desc):
	global data
	for chunk in tqdm(range(1,num_chunks+1)):
		tasks=[]
		repos=[]
		for idx in range((chunk-1)*num_processors,(chunk-1)*num_processors+num_processors):
			repos+=[desc.iloc[idx]["repo"]]
			tasks+=[asyncio.create_task(getTopics(model,desc.iloc[idx]["desc"],desc.iloc[idx]["repo"],q))]
		try:
			results=await asyncio.gather(*tasks) 
			for repo,r in zip(repos,results):
				topics=parseTopic(r)
				data+=[[repo,",".join(topics)]]
		except:
			#raise ValueError("Error")
			print(f"waiting {datetime.now()}")
			time.sleep(60)

			tasks=[]
			repos=[]
			for idx in range((chunk-1)*num_processors,(chunk-1)*num_processors+num_processors):
				repos+=[desc.iloc[idx]["repo"]]
				tasks+=[asyncio.create_task(getTopics(model,desc.iloc[idx]["desc"],desc.iloc[idx]["repo"],q))]
			
			results=await asyncio.gather(*tasks) 
			for repo,r in zip(repos,results):
				topics=parseTopic(r)
				data+=[[repo,",".join(topics)]]

		finally:
			convertTopicDF()


def convertTopicDF():
	df = pd.DataFrame(np.array(data),columns=["repo","topics"])
	df.to_csv("geminiTopics.csv")

def getTopicEmbedding(repo=None):
	# Your list of words
	try:
		words=["no-tags"]
		if(repo["topics"] is not None and type(repo["topics"])==str):
			words = repo["topics"].split(",")

		# Generate embeddings for the list of words
		embeddings = genai.embed_content(
		    model="models/text-embedding-004",
		    content=words
		)

		return words, embeddings["embedding"]
	except Exception as e:
		print(repo["topics"])
		print(words)
		print(e)


if __name__ == '__main__':
	initApi()

	desc=pd.read_csv("en_desc.csv",names=["oldidx","repo","desc"],header=0)
	desc["repo"]=desc["repo"].apply(lambda x:x.strip())
	desc["desc"]=desc["desc"].apply(lambda x:x.strip())

	#model = genai.GenerativeModel('gemini-1.5-flash')
	#q = queue.Queue()
	#num_chunks = len(desc) // num_processors
	#st=time.time()
	#asyncio.run(processParallel(num_chunks,desc))
	#convertTopicDF()

	topics=pd.read_csv("geminiTopics.csv")
	analyzed_topics=[]
	analyzed_embenddings=[]
	results_embenddings=[]
	for i in tqdm(range(topics.shape[0])):
		repo=topics.iloc[i]
		words,embeddings=getTopicEmbedding(repo=repo)
		analyzed_topics+=words
		analyzed_embenddings+=embeddings
		# Create a list of dictionaries with 'repo' and 'topics' keys
		results_embedding=pd.DataFrame([{'topic': topic, 'embedding': analyzed_embenddings[i]} for i, topic in enumerate(analyzed_topics)],columns=["topic","embedding"])
		results_embedding.to_csv("topic_embedding.csv",index=False)


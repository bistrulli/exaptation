from pathlib import Path
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
import pickle
import traceback


chainPath=Path("/home/ubuntu/chains")

num_processors = os.cpu_count()*10
model=None
data=[]

def initApi():
	GOOGLE_API_KEY=var = os.environ['GOOGLE_API_KEY']
	genai.configure(api_key=GOOGLE_API_KEY)

def get_embeddings_batch_with_backoff(topics=None, max_retries=10):
	"""
	Genera gli embedding per un batch di parole utilizzando la Google Gemini API con gestione del rate-limit.
	
	Args:
		words (list): Lista di parole per le quali generare gli embedding.
		max_retries (int): Numero massimo di tentativi in caso di errore 429.
	
	Returns:
		dict: Un dizionario con ogni parola e il suo embedding associato.
	"""
	if(topics is None):
		raise TypeError(f"topic must not be None.") 

	retries = 0
	while retries < max_retries:
		try:
			# Chiama l'API per generare embedding
			#response = gemini.generate_embeddings(input=words)
			# response = genai.embed_content(
			# 	model="models/text-embedding-004",
			# 	content=words
			# )
			# Chiama il metodo embed_content per generare gli embedding
			response = genai.embed_content(
				model="models/text-embedding-004",
				content=topics
			)
			# Estrai gli embedding e associa ogni contenuto al suo embedding
			embeddings = {content: embedding for content, embedding in zip(topics, response['embedding'])}
			return embeddings
		except Exception as e:
			if "429" in str(e):  # Controlla se si tratta di un errore di rate limit
				wait_time = 2 ** retries  # Backoff esponenziale: 2^retries secondi
				print(f"Errore 429: rate limit superato. Riprovo tra {wait_time} secondi...")
				time.sleep(wait_time)
				retries += 1
			else:
				# Logga altri errori e interrompi
				traceback.print_exc()
				print(f"Errore durante la generazione degli embedding: {e}")
				break
	print("Numero massimo di tentativi superato. Interrotto.")
	return None

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

def getTopicEmbedding(topics=None):
	if(topics is None):
		raise TypeError(f"topic must not be None.") 

	try:
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

def getEmbedding(jsonchain=None):
	embeddings = []
	repos = []
	idx = 0
	
	# Outer tqdm to track progress over top-level keys
	for key, val in tqdm(enumerate(jsonchain), desc="Processing keys"):
		# Inner tqdm to track progress over levels within each key
		for lvl, val2 in tqdm(enumerate(jsonchain[val]), desc="Processing levels", leave=False):
			if val2 != "duration":
				# Innermost tqdm to track progress over dependencies
				for dep in tqdm(jsonchain[val][val2], desc="Processing dependencies", leave=False):
					if "-->" in dep:
						repo_dep = dep.split("-->")[-1].strip()
						if repos_topic[repos_topic["repo"] == repo_dep].shape[0] > 0:
							repo = repos_topic[repos_topic["repo"] == repo_dep]
							embeds = getTopicEmbedding(repo=repo)
							embeddings.append(embeds[1][0])
							repos.append(repo_dep)
							idx += 1
							time.sleep(2)
							if(idx%100==0):
								# Open the file in binary write mode
								embeddings_file = open(f'embeddings_{list(jsonchain.keys())[0].replace("/","_")}.pkl', "wb")
								repos_file = open(f'repos_{list(jsonchain.keys())[0].replace("/","_")}.pkl', "wb")
								# Save the data
								pickle.dump(embeddings, embeddings_file)
								pickle.dump(repos, repos_file)
								# Close the file manually
								embeddings_file.close()
								repos_file.close()
								#print("Data saved successfully!")
						else:
							# Uncomment to enable logging for repos not found
							# print(f"repo {repo_dep} not found")
							pass
	return embeddings, repos

def readJsonChain(chain=None):
	jsonchain=None
	if(Path(chain).is_file()):
		content=chain.read_text()
		jsonchain = json.loads(content)
	else:
		raise ValueError(f"{chain} not found!")
	return jsonchain



if __name__ == '__main__':
	initApi()

	# desc=pd.read_csv("en_desc.csv",names=["oldidx","repo","desc"],header=0)
	# desc["repo"]=desc["repo"].apply(lambda x:x.strip())
	# desc["desc"]=desc["desc"].apply(lambda x:x.strip())

	#model = genai.GenerativeModel('gemini-1.5-flash')
	#q = queue.Queue()
	#num_chunks = len(desc) // num_processors
	#st=time.time()
	#asyncio.run(processParallel(num_chunks,desc))
	#convertTopicDF()

	# topics=pd.read_csv("geminiTopics.csv")
	# #df=pd.read_csv("topic_embedding.csv")
	# analyzed_topics=[]
	# analyzed_embenddings=[]
	# results_embenddings=[]
	# try:
	# 	for i in tqdm(range(topics.shape[0])):
	# 		repo=topics.iloc[i]
	# 		words,embeddings=getTopicEmbedding(repo=repo)
	# 		analyzed_topics+=words
	# 		analyzed_embenddings+=embeddings
	# 		time.sleep(1)
	# except Exception as e:
	# 	print(e)
	# finally:
	# 	# Create a list of dictionaries with 'repo' and 'topics' keys
	# 	results_embedding=pd.DataFrame([{'topic': topic, 'embedding': analyzed_embenddings[i]} for i, topic in enumerate(analyzed_topics)],columns=["topic","embedding"])
	# 	results_embedding.to_csv("topic_embedding.csv",index=False)


	#initApi()
	repos_topic=pd.read_csv("geminiTopics.csv")
	#jsonchain=readJsonChain(chain=chainPath/Path("chains_1000_iteration.json"))
	embeddings=get_embeddings_batch_with_backoff(topics=["stronzo"])
	if embeddings:
		for word, embedding in embeddings.items():
			print(f"Embedding per '{word}': {embedding}")

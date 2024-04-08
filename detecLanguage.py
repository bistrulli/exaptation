from langdetect import detect_langs
import pandas as pd
from tqdm import tqdm

def detect_language(line): 
	try: 
		langs = detect_langs(line) 
		for l in langs:
			return l.lang, l.prob 
	except: 
		return "err", 0.0 

if __name__ == '__main__':
	df=pd.read_csv("./description.csv",delimiter="|",names=["A"])
	print(df.shape)
	# df=df["A"].str.split("╡",n=1, expand=True)
	# idx=[]
	# for i in tqdm(range(df.shape[0])):
	# 	if(detect_language(df[1].iloc[i])[0]=="en"):
	# 		idx+=[i]
	# df.iloc[idx].to_csv("en_desc.csv")
	print(pd.read_csv("./en_desc.csv").shape)
import os
from codecs import open
import pandas as pd
for filename in ["train.txt","test.txt"]:

	fin=filename
	df= pd.read_csv(fin,sep="\t",encoding="utf-8",quoting=3)
	df[["#1 String", "#2 String","Quality"]].to_csv(filename,index=False,header=None,encoding="utf-8",sep="\t")
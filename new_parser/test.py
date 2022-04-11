import pandas as pd
import csv
import re
df = pd.read_csv("ha_csv_new2.csv")
mylist = list()
for i in range(0,11):
    data=df["HA 1"][i]
    faculty=df["Faculty"][i]
    data2 = data.split(",")
    for j in data2:
        newitem = re.sub('[^a-zA-Z0-9]+', '', j)
        mylist.append({"Faculty":faculty, "Module_Code": newitem})


for key, item in all_modules:
    for key2, item2 in ha_modules:
        
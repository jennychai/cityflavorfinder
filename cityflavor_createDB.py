import MySQLdb
import json
from pandas import DataFrame
#import pandas as pd
import pandas.io.sql as psql
import nltk
from nltk.corpus import wordnet
from nltk.corpus import stopwords
import re
import random
from itertools import chain
from collections import Counter
from nltk.corpus import stopwords

m = re.compile('\d')
english_stop_words=stopwords.words('english')
db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
db.autocommit(True)
cursor = db.cursor()
cursor.execute("USE bestfood")

def get_jsons():
    #path_review_json='/Users/xiaoqian/insight/yelp_phoenix_academic_dataset/yelp_academic_dataset_review.json'
    #path_business_json='/Users/xiaoqian/insight/yelp_phoenix_academic_dataset/yelp_academic_dataset_business.json'
    path_data_json='/Users/xiaoqian/insight/yelp_academic_dataset.json'
    data = [json.loads(line) for line in open(path_data_json)]
    #fh = open(path_data_json)
    #data=[]
    #counter = 0
    # open the reviews json file
    
    """for line in fh:
        if counter < 50000:
            data.append(json.loads(line))
            counter += 1
    """
    restaurants =[]
    reviews = [] 
    for i in xrange(len(data)):
        #if data[i]['type'] == 'review':
        #    reviews.append(data[i])
        #elif data[i]['type'] == 'business':
        if data[i]['type'] == 'business':
            if 'Restaurants' in data[i]['categories']:
                restaurants.append(data[i])
    busi_frame = DataFrame(restaurants)
    review_frame = DataFrame(reviews)
    return busi_frame, review_frame

def create_tables():
    db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
    db.autocommit(True)
    cursor = db.cursor()
    cursor.execute("USE bestfood")
    with db:
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS Acad_Restaurants")
        cursor.execute("CREATE TABLE Acad_Restaurants(Id INT PRIMARY KEY AUTO_INCREMENT, bid VARCHAR(25), City VARCHAR(50), Name VARCHAR(100),  Stars INT, review_count INT, schools TEXT, address TEXT, url TEXT)")
        cursor.execute("DROP TABLE IF EXISTS Acad_Reviews")
        cursor.execute("CREATE TABLE Acad_Reviews(Id INT PRIMARY KEY AUTO_INCREMENT, text TEXT, bid VARCHAR(25), Stars INT, City VARCHAR(50), schools TEXT, address TEXT)")
        cursor.execute("DROP TABLE IF EXISTS Acad_top1grams")
        cursor.execute("CREATE TABLE Acad_top1grams(Id INT PRIMARY KEY AUTO_INCREMENT, homecity VARCHAR(50), visitcity VARCHAR(50), term VARCHAR(100), ratio VARCHAR(50))")

    db.close()

def populate_busi_table(busi_frame):
    restaurant_id_list =[]
    db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
    db.autocommit(True)
    cursor = db.cursor()
    cursor.execute("USE bestfood")
    with db:
        for i in range(0,len(busi_frame)):
         #for i in range(0,10):
            if 'Restaurants' in busi_frame['categories'][i]:
                name = busi_frame['name'][i]
                city = busi_frame['city'][i]
                bid  = busi_frame['business_id'][i]
                stars = busi_frame['stars'][i]
                review_count = busi_frame['review_count'][i]
                address = busi_frame['full_address'][i]
                schools = busi_frame['schools'][i]
                url = busi_frame['url'][i]
                restaurant_id_list.append(bid);
                #sql="""insert into Restaurants (bid, City, Name) VALUES (%s,%s,%s)"""
                sql='insert into Acad_Restaurants (bid, City, Name, Stars, review_count,schools, address,url) VALUES  ("%s","%s","%s", "%d","%d", "%s", "%s","%s")' % (bid,city,name,stars,review_count, schools, address,url)
                if len(name) > 70:
                    print "Business name too long!"
                else:
                    #cursor.execute(sql,(bid,city,name))
                    cursor.execute(sql)
    db.close()         

def populate_review_tables(review_frame,busi_frame):      
    db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
    db.autocommit(True)
    cursor = db.cursor()
    cursor.execute("USE bestfood")  
    ##sql = "SELECT bid from acad_restaurants"
    #df_mysql = psql.frame_query(sql, con=db)
    #rest_ids = df_mysql['bid']
    for i in  range(47789,len(review_frame)):
        bid = review_frame['business_id'][i]
        #print bid
        bframe = busi_frame[busi_frame['business_id'] ==  bid]
        #print bframe
        if len(bframe) >0: 
            reviewText = review_frame['text'][i]
            reviewText = reviewText.encode('ascii','ignore')
            reviewText = reviewText.replace("\n"," ")
            reviewText = reviewText.replace("\'"," ")
            reviewText = reviewText.replace("(","")
            reviewText = reviewText.replace(")","")
            reviewText = reviewText.replace('"','')
            reviewText = reviewText.replace('-',' ')
            reviewText = reviewText.replace('!',' ')
            reviewText = reviewText.replace(',',' ')
            reviewText = reviewText.replace('.','')
            reviewText = reviewText.replace("\\","")
            city  = bframe.city
            city = city.tolist()
            city = city[0]
            schools = bframe.schools
            address = bframe.full_address
            Stars = review_frame['stars'][i]
            sql='insert into Acad_Reviews (text, bid, Stars,city,schools,address) VALUES  ("%s", "%s","%d","%s","%s", "%s")' % (reviewText,bid,Stars,city, schools,address)
            cursor.execute(sql)       
            print i, "inserted!"
           

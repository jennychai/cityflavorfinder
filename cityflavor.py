import utils
import MySQLdb
#import json
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
from nltk import bigrams


m = re.compile('\d')
english_stop_words=stopwords.words('english')

def get_db_connection():
    db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
    db.autocommit(True)
    cursor = db.cursor()
    cursor.execute("USE bestfood")
    return db, cursor

   
def classify_cities(city1, city2,NCommonWords, db, cursor):
    if not 'city1' in locals():
        city1 = 'austin'
    if not 'city2' in locals():
        city2 = 'cambridge'
        
    #get 1grams and bigrams from reviews for home and visit city restaurants   
    city1_1gram_list, city1_bigram_list = get_reviews_city_from_db(city1, db)
    city2_1gram_list, city2_bigram_list = get_reviews_city_from_db(city2, db)
    
    #train on both 1grams and bigrams
    city1_list = city1_1gram_list + city1_bigram_list
    city2_list = city2_1gram_list + city2_bigram_list
    random.shuffle(city1_list)
    random.shuffle(city2_list)
    classifier12 = run_classifier(city1_list, city2_list, NCommonWords, city1, city2)  

    #train on 1grams
    #classifier1 = run_classifier(city1_1gram_list, city2_1gram_list, NCommonWords)  
    #train on the bigrams
    #classifier2 = run_classifier(city1_bigram_list,city2_bigram_list,NCommonWords)  
    #dictHomeCity, dictVisitCity = get_list_of_useful_features(classifier1,100,city1,city2)  
    #bidictHomeCity, bidictVisitCity = get_list_of_useful_features(classifier2,100,city1,city2)  
    dictHomeCity, dictVisitCity = get_list_of_useful_features(classifier12,1000,city1,city2)  
    utils.write_results_to_DB(dictHomeCity, dictVisitCity,city1, city2, db)
    
    #return classfier1, classifier2, classifier12
    #return classifier12
    
    #get recommended top N items for home and visit cities
    #recHomeCity12 = find_top_items12(dictHomeCity12)
    #recVisitCity12  = find_top_items12(dictVisitCity12)
    #recHomeCity = find_top_items(dictHomeCity,bidictHomeCity,5)
    #recVisitCity = find_top_items(dictVisitCity,bidictVisitCity,5)
    #return recHomeCity, recVisitCity

# Find restaurants with the most number of reviews that contained the food item        
## make sure we have equal number of reviews in each city
## downsample the one with more reviews
def match_review_lengths(city1_orig_list, city2_orig_list):
    random.shuffle(city1_orig_list)
    random.shuffle(city2_orig_list)
    if len(city1_orig_list) > len(city2_orig_list):
        city1_list = city1_orig_list[0:len(city2_orig_list)]
        city2_list = city2_orig_list
    else:
        city2_list = city2_orig_list[0:len(city1_orig_list)]
        city1_list = city1_orig_list
        
    return city1_list, city2_list

def run_classifier(city1_words, city2_words, nCommonWords, city1, city2):
    all_words1=Counter()
    city1_word_list, city2_word_list = match_review_lengths(city1_words, city2_words)
    for tokens in city1_word_list + city2_word_list:
        for token in tokens:
            all_words1[token]+=1
    
  
    #all_words1 = remove_duplicates(all_words1)
    most_common=all_words1.most_common(nCommonWords)
    #most_common=zip(*most_common)[0]
    #a=map(list,zip(*most_common))
    #most_commonN = a[0]
    #print 'most_common_words = ',most_common[1:20]
    # map(list, zip(*[(1, 2), (3, 4), (5, 6)]))
    threshold = 5e-4*len(all_words1)
    print "threshold is", threshold
    feature_words = []
    for w in most_common:
        if w[1] > threshold:
               feature_words.append(w[0])
    
    def document_features(tokens):
        #return {word:word in tokens for word in most_common}
        return {word:word in tokens for word in feature_words}

    set1=[(document_features(tokens), city1) for tokens in city1_word_list]
    set2=[(document_features(tokens), city2) for tokens in city2_word_list]

    featuresets= set1 + set2
    random.shuffle(featuresets) 
    size = int(len(featuresets) * 0.1)
    train_set, test_set = featuresets[size:], featuresets[:size]
    classifier = nltk.NaiveBayesClassifier.train(train_set)

    print 'accuracy',nltk.classify.accuracy(classifier, test_set)

    classifier.show_most_informative_features(100)
    return classifier
    
def get_list_of_useful_features(classifier, n, from_city, to_city):
        # Determine the most relevant features, and display them.
        cpdist = classifier._feature_probdist
        print('Most Informative Features')
        dict_home_city ={}
        dict_visit_city ={}
        for (fname, fval) in classifier.most_informative_features(n):
            def labelprob(l):
                return cpdist[l,fname].prob(fval)
            labels = sorted([l for l in classifier._labels
                             if fval in cpdist[l,fname].samples()],
                            key=labelprob)
            if len(labels) == 1: continue
            l0 = labels[0]
            l1 = labels[-1]
            if cpdist[l0,fname].prob(fval) == 0:
                ratio = 'INF'
            else:
                ratio = '%8.1f' % (cpdist[l1,fname].prob(fval) /
                                  cpdist[l0,fname].prob(fval))
            print(('%24s = %-14r %6s : %-6s = %s : 1.0' %
                   (fname, fval, str(l1)[:6], str(l0)[:6], ratio)))
            if l1 == from_city:
                dict_home_city[fname] = ratio
            elif l1 == to_city:
                dict_visit_city[fname] = ratio
        return dict_home_city, dict_visit_city

## combine the 1gram and bigrams to get top list
def find_top_items12(dict12):
    reclist = []

    reclist = list(sorted(dict12, key=dict12.__getitem__, reverse=True))
    
    reclist = remove_plurals_from_list(reclist)  
    return reclist

def tokenize(text):
        tokens=nltk.word_tokenize(text)
        # strip out trailing puncutation
        tokens = [ token[:-1] if token[-1] in ['.',',','!','?'] else token for token in tokens]

        # lower case
        tokens = [token.lower() for token in tokens]

        # Take only relativly long characters
        tokens = [token for token in tokens if len(token)>=3]

        # remove words with numbers/digits
        tokens = [token for token in tokens if m.search(token) is None]

        # Remove stop words: http://nltk.googlecode.com/svn/trunk/doc/book/ch02.html
        tokens = [token for token in tokens if token not in english_stop_words]
        return tokens



def get_reviews_city_from_db(city, db):
    tokens_list =[]
    bigram_list = []
    if not 'city' in locals():
        city = 'new york'
    sql = "SELECT bid, text,city from acad_reviews WHERE city = \'"+city+"\' AND Stars >= 4"
    df_mysql = psql.frame_query(sql, con=db)
    sql = "SELECT distinct name from acad_restaurants WHERE city = \'"+city+"\'"
    df_rest = psql.frame_query(sql, con=db)

    for i in  xrange(len(df_mysql)):
        ones = []
        bis= []
        text = df_mysql['text'][i]
        city = df_mysql['city'][i]
        text = re.sub(city,'',text)
        # remove name of restaurants from review text
        for j in  xrange(len(df_rest)):
            rname = df_rest['name'][j]
            text = re.sub(rname,'',text)
        
        tokens = tokenize(text)
        
        # get bigrams
        if len(tokens) < 2:
            tokens = 'dummy dummy'
        review_bigrams = bigrams(tokens)
        for t in tokens:
            if utils.is_food(t):
                ones.append(t)
        for t in review_bigrams:
            if utils.is_food(t):
                t=t[0] +" "+ t[1]
                bis.append(t)
                                
        tokens_list.append(ones)
        bigram_list.append(bis)
    return tokens_list,bigram_list
       
def main():
    db, cursor = get_db_connection()
    #classify_cities('waterloo','austin',1000, db, cursor)
    classify_cities('cambridge','berkeley',1000, db, cursor)

    #classifier_cambridge_houston = classify_cities('houston','cambridge',1000)
    #classifier_cambridge_philadelphia = classify_cities('philadelphia','cambridge',1000)
    #classifier_providence_atlanta = classify_cities('providence','atlanta',1000)
    #classifier_philadelphia_waterloo = classify_cities('philadelphia','waterloo',1000)
    



if __name__ == '__main__':
    main()

   

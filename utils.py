#!/usr/bin/env python
"""
utils.py

"""
import re
from nltk.corpus import stopwords
from nltk.corpus import wordnet
import pickle

m = re.compile('\d')
english_stop_words=stopwords.words('english')

def remove_plurals_from_list(wordlist):
    for word in wordlist:
        if (word + 's') in wordlist:
            plural = word +'s'
            wordlist.remove(plural)
    return wordlist

def remove_redundant_features(features):
    removeItems=[]
    features = remove_plurals_from_list(features)  
    for i in range(0,len(features)-1):
        currentItem = features[i]
        for j in range(i+1,len(features)):
            if inTerm(currentItem, features[j]):
                removeItems.append(currentItem)
    for r in removeItems:
        features = features.remove(r)   
    return features     

    
    
            
def isPlural(word1, word2):
    """
    Compare two words to see if one is the plural of another
    (limited to pluralities ending in "s")

    return: True/False
    params:
            word1: string | to be compared with word2
            word2: string | to be compared with word2
    """
    # if neither word ends in "s", return false
    if word1[-1] != 's' and word2[-1] != 's':
        return False
    # otherwise check word1/word2 for 's'-removed similarity
    return word2[:-1] == word1 or word1[:-1] == word2

def inTerm(word1, word2):
    """
    Compare two words to see if one is inside the other

    return: True/False
    params:
            word1: string | to be compared with word2
            word2: string | to be compared with word2
    """
    return word1 in word2 or word2 in word1


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
        if data[i]['type'] == 'review':
            reviews.append(data[i])
        elif data[i]['type'] == 'business':
            if 'Restaurants' in data[i]['categories']:
                restaurants.append(data[i])
    busi_frame = DataFrame(restaurants)
    review_frame = DataFrame(reviews)
    return busi_frame, review_frame

def is_food(term):
    isFood = False
    isLocation = False
    if isinstance(term,str):
        #single words
       synsets = wordnet.synsets(term)
       for synset in synsets:
           if 'food' in synset.lexname:
               isFood = True
           if 'location' in synset.lexname:
               isLocation = True
    else:
    # must be a bigram or trigram 
        for t in term:
            synsets = wordnet.synsets(t)
            for synset in synsets:
                if ('food' in synset.lexname):
                    isFood = True
    if isLocation:
        isFood = False
    return isFood

                            
def get_restaurant_names(city):
    tokens_list =[]
    if not 'city' in locals():
        city = 'Cambridge'
    sql = "SELECT distinct(name) from acad_restaurants WHERE city = \'"+city+"\'"
    df_mysql = psql.frame_query(sql, con=db)
    for i in  range(0,len(df_mysql)):
        name = df_mysql['name'][i]
        tokens_list.append(tokenize(name))
    return tokens_list

def write_results_to_DB(dictHomeCity, dictVisitCity,homecity, visitcity, db):
    home_list = find_top_items12(dictHomeCity)
    visit_list = find_top_items12(dictVisitCity)
    insert_bestfood(home_list,homecity,visitcity,db)
    insert_bestfood(visit_list,visitcity,homecity,db)

## combine the 1gram and bigrams to get top list
def find_top_items12(dict12):
    reclist = []

    reclist = list(sorted(dict12, key=dict12.__getitem__, reverse=True))
    
    reclist = remove_plurals_from_list(reclist)  
    return reclist


def find_popularity_ratio(food,city1,city2,db):
    sql = "select count(*) from Acad_reviews where city = \'"+city1+"\' AND stars >=4"
    df_count = psql.frame_query(sql,con=db)
    total_reviews_city1 = df_count['count(*)']
    sql = "select count(*) from Acad_reviews where city = \'"+city2+"\' AND stars >=4"
    df_count = psql.frame_query(sql,con=db)
    total_reviews_city2 = df_count['count(*)']
    sql = "select count(*) from Acad_reviews where city = \'"+city1+"\' AND text like \'%"+food+"%\' AND stars >= 4"
    df_count = psql.frame_query(sql,con=db)
    reviews_city1 = df_count['count(*)']
    sql = "select count(*) from Acad_reviews where city = \'"+city2+"\' AND text like \'%"+food+"%\' AND stars >= 4"
    df_count = psql.frame_query(sql,con=db)
    reviews_city2 = df_count['count(*)']
    pop1 = float(reviews_city1)/float(total_reviews_city1)
    pop2 = float(reviews_city2)/float(total_reviews_city2)
    ratio = (int)(pop1/pop2)
    return ratio
    
    
def find_restaurant_for_food(food, city,db):
    sql = "select bid from Acad_reviews where city = \'"+city+"\' AND text like \'%"+food+"%\' AND stars > 4 order by bid"
    df_bid = psql.frame_query(sql, con=db)
    bids = df_bid['bid']
    bid_counter = Counter(bids)
    top3 = bid_counter.most_common(3)
    topRest=[]
    for item in top3:
        bid = item[0]
        sql = "select name,url from acad_restaurants where bid =\'"+bid+"\'"
        df_rest = psql.frame_query(sql, con=db)
        rname = df_rest['name'][0]
        url = df_rest['url'][0]
        rec=[rname,url]
        topRest.append(rec)
    return topRest



def insert_bestfood(foodlist, homecity,visitcity,db):
    #create table acad_topitems(homecity VARCHAR(25), visitcity VARCHAR(25), term VARCHAR(100), rank INT, rest VARCHAR(100), url TEXT)
    cursor = db.cursor()
    cursor.execute("USE bestfood")
    for i in xrange(len(foodlist)):
        term = foodlist[i]
        # get the top 3 places for this food
        topRest = find_restaurant_for_food(term,homecity,db)
        rest = topRest[0][0]
        url = topRest[0][1]
        sql='insert into acad_topitems(homecity, visitcity, term, rank,rest,url) VALUES  ("%s","%s","%s", %d,"%s","%s")' % (homecity,visitcity,term,i+1,rest,url)
        cursor.execute(sql)       
    db.commit()

def save_to_pickle(data, filename):
    output = open(filename, 'wb')

    # Pickle dictionary using protocol 0.
    pickle.dump(data, output)

    # Pickle the list using the highest protocol available.
    #pickle.dump(selfref_list, output, -1)
    output.close()
    
def get_pickle_data(filename):
    pkl_file = open(filename, 'rb')

    data = pickle.load(pkl_file)
    #data2 = pickle.load(pkl_file)
    pkl_file.close()
    return data
    

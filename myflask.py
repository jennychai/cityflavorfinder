from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
#from analye import get_top_food
import MySQLdb
import pandas.io.sql as psql
import random
from nltk.corpus import wordnet
from collections import Counter


app = Flask(__name__)

# HOME display mulitple tab ## not working yet... 
@app.route('/layout')
def home():
        return render_template('layout.html')

@app.route('/about')
def home():
        return render_template('about.html')

@app.route('/test')
def home():
        return render_template('d3test.html')

#display form to get user input (city name)
@app.route('/',methods = ['GET','POST'])
@app.route('/start',methods = ['GET','POST'])
def start():
        return render_template('start.html')

# get user input from templates/start.html and pass on to analysis script
@app.route('/find', methods = ['POST'])
def find():
    rec =[]
    homecity = request.form['homecity']
    visitcity = request.form['visitcity']
    if not homecity:
        homecity = 'atlanta'
    if not visitcity:
        visitcity = 'new york'
    db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = '', db = 'bestfood')
    cursor = db.cursor()
    cursor.execute("USE bestfood")
    sql = "select * from Acad_topitems where homecity=\'"+visitcity+"\' AND visitcity= \'"+homecity+"\'  order by rank asc limit 4"
    df_mysql = psql.frame_query(sql, con=db)
    foodlist =[]
    for i in range(0,len(df_mysql)):
        food = df_mysql['term'][i]
        rname = df_mysql['rest'][i]
        url = df_mysql['url'][i]
        ratio = df_mysql['popularity_ratio'][i]
   	# figure out which restaurant for the food item
  	#sql = "select bid from Acad_reviews where city = \'"+visitcity+"\' AND text like \'%"+food+"%\' order by stars desc limit 1"
	#df_bid = psql.frame_query(sql, con=db)
	#bid = df_bid['bid'][0]
	#sql = "select name,url from acad_restaurants where bid =\'"+bid+"\'"
	#df_rest = psql.frame_query(sql, con=db)
	
	"""
	topRests = find_restaurant_for_food(food,visitcity,db)
	rname = topRests[0][0]
	url = topRests[0][1]
	"""
	#rname = df_rest['name'][0]
	#url = df_rest['url'][0]
	#rname = 'dummy'
	#url = 'dummy url'
	rec = [food,rname,url,ratio]
        foodlist.append(rec)
    wordlist=[]
    wordlist.append(rec)
    wordlist.append(visitcity)
    #random.shuffle(foodlist)
    return render_template('results.html', visitcity = visitcity, wordlist = foodlist) 
    #return render_template('results.html', wordlist = wordlist) 


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
                    

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    #port = int(os.environ.get('PORT', 5000))
    app.debug = True
    #app.run(host='0.0.0.0', port=port)
    app.run()

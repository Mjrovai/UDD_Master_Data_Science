import botometer
import tweepy

from flask import Flask, request, g, redirect, url_for, render_template, flash, make_response
import requests
import time
import os
import io

auth = tweepy.OAuthHandler(os.environ['consumer_key'], os.environ['consumer_secret'])
auth.set_access_token(os.environ['access_token'], os.environ['access_token_secret'])
api = tweepy.API(auth)

mashape_key = os.environ['mashape_key']
twitter_app_auth = {
    'access_token' : os.environ['access_token'],
    'access_token_secret' : os.environ['access_token_secret'],
    'consumer_key' : os.environ['consumer_key'],
    'consumer_secret' : os.environ['consumer_secret']    
}

bom = botometer.Botometer(wait_on_ratelimit = True, mashape_key = mashape_key, **twitter_app_auth)

def get_raw_tweets(screen_name):
    tweets = api.user_timeline(screen_name=screen_name,
                               count=200,
                               tweet_mode='extended')
    return tweets

def get_user_info(tweets):
    item = tweets[0].user
    screen_name = item.screen_name
    last_tw = tweets[0]
    older_tw = tweets[-1]
    id = item.id
    name = item.name
    photo = item.profile_image_url
    local = item.location
    if local == '': local = "No Location"
    if item.description == "":
        description = False
    else:
        description = True
    tweets_count = item.statuses_count
    friends_count = item.friends_count
    followers_count = item.followers_count
    favourites_count = item.favourites_count
    tweets_analysed = len(tweets)
    last_tweet_date = last_tw.created_at
    older_tweet_date = older_tw.created_at
    return screen_name, id, name, photo, local, description, tweets_count, friends_count, followers_count, favourites_count, item, last_tweet_date, older_tweet_date, tweets_analysed

def tweet_stat(item, last_tweet_date, older_tweet_date, tweets_analysed):
    tweets_cnt = item.statuses_count
    account_created_date = item.created_at  
    delta = last_tweet_date - account_created_date
    recent_delta = last_tweet_date - older_tweet_date
    account_age_days = delta.days
    recent_age_days = recent_delta.days
    if account_age_days > 0:
        ave_acc_tw_day = round(tweets_cnt/account_age_days, 2)
        ave_recent_tw_day = round(tweets_analysed/recent_age_days, 2)
    return account_age_days, ave_acc_tw_day, ave_recent_tw_day

def get_rt_hashtags_mentions(tweets):    
    hashtags = []
    mentions = []
    retweets_cnt = 0
    tweet_count = 0
    ntw = len(tweets)
    if ntw != 0:
        for i in range(ntw):
            if tweets[i].retweet_count != 0: 
                retweets_cnt+=1   
    for status in tweets:       
        if hasattr(status, "entities"):
            entities = status.entities
            if "hashtags" in entities:
                for ent in entities["hashtags"]:
                    if ent is not None:
                        if "text" in ent:
                            hashtag = ent["text"]
                            if hashtag is not None:
                                hashtags.append(hashtag)
            if "user_mentions" in entities:
                for ent in entities["user_mentions"]:
                    if ent is not None:
                        if "screen_name" in ent:
                            name = ent["screen_name"]
                            if name is not None:
                                mentions.append(name)
    
    rt_ratio = round((retweets_cnt/ntw)*100)
    unique_mentions_count = len(set(mentions))
    unique_hashtags_count = len(set(hashtags))
    mentions_count = len(mentions)
    hashtags_count = len(hashtags)
    try:
        ment_idx = round(unique_mentions_count/mentions_count, 2)
    except:
        ment_idx = 0.0
    try:
        hash_idx = round(unique_hashtags_count/hashtags_count, 2) 
    except:
        hash_idx = 0.0
    
    return mentions, hashtags, mentions_count, hashtags_count, unique_mentions_count, unique_hashtags_count, ment_idx, hash_idx, rt_ratio


def get_bot_prob(user):
    try:
        result = bom.check_account(user)
        sc_name = ((result['user']['screen_name']))
        score = int((result['scores']['universal']) * 100)
        id = int((result['user']['id_str']))
        user = '@' + sc_name
        return user, id, score
    except:
        return 'Not a Twitter user', 0, 0

def get_all_metrics (user):
    try:
        raw_tweets = get_raw_tweets(user)
        user, id, name, photo, loc, descr, tws_cnt, frs_cnt, fols_cnt, fav_cnt, item, last_tweet_date, older_tweet_date, tweets_analysed = get_user_info(raw_tweets)
        acc_age_days, ave_tw_day, ave_recent_tw_day = tweet_stat(item, last_tweet_date, older_tweet_date, tweets_analysed)          
        _, _, mentions_cnt, hashtags_cnt, unique_mentions_cnt, unique_hashtags_cnt, ment_idx, hash_idx, rt_ratio = get_rt_hashtags_mentions(raw_tweets)
        return user, id, name, photo, loc, descr, tws_cnt, frs_cnt, fols_cnt, fav_cnt, item, last_tweet_date, older_tweet_date, tweets_analysed, acc_age_days, ave_tw_day, ave_recent_tw_day, mentions_cnt, hashtags_cnt, unique_mentions_cnt, unique_hashtags_cnt, ment_idx, hash_idx, rt_ratio
    except:
        return 'Not a Tweeter user', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        
    
app = Flask(__name__) 

user = ''
id = 0
prob = 0

@app.route('/')
def index():
  
    templateData = { 
        'user': user,
        'id': id,
        'prob': prob
    }
    return render_template('index.html', **templateData)

@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    if request.method == 'POST':
        user = request.form['user']
        user, id, prob = get_bot_prob(user)

        templateData = {
            'user': user,
            'id': id,
            'prob': prob
        }
    return render_template('index.html', **templateData)

@app.route('/metrics', methods=['GET', 'POST'])
def user_data():
    """User data (metrics) home page."""
    if request.method == 'POST':
        user = request.form['user']
        timeNow = time.asctime( time.localtime(time.time()) )
        user, id, name, photo, loc, descr, tws_cnt, frs_cnt, fols_cnt, fav_cnt, item, last_tweet_date, older_tweet_date, tweets_analysed, acc_age_days, ave_tw_day, ave_recent_tw_day, mentions_cnt, hashtags_cnt, unique_mentions_cnt, unique_hashtags_cnt, ment_idx, hash_idx, rt_ratio = get_all_metrics (user)
        
        templateData = {
            'time': timeNow,
            'id': id, 
            'user':user,
            'name': name,
            'photo': photo,
            'loc': loc, 
            'descr': descr, 
            'tws_cnt': tws_cnt, 
            'frs_cnt': frs_cnt, 
            'fols_cnt': fols_cnt, 
            'fav_cnt': fav_cnt,
            'tweets_analysed': tweets_analysed,
            'last_tweet_date': last_tweet_date,
            'older_tweet_date': older_tweet_date,
            'acc_age_days': acc_age_days,
            'ave_tw_day': ave_tw_day,
            'ave_recent_tw_day': ave_recent_tw_day,
            'rt_ratio': rt_ratio,
            'mentions_cnt': mentions_cnt,
            'ment_idx': ment_idx,
            'hashtags_cnt':hashtags_cnt,
            'hash_idx':hash_idx
        }
        return render_template('metrics.html', **templateData)
    
@app.route('/block', methods=['GET', 'POST'])
def block_user():
    """Block User page."""
    if request.method == 'POST':
        user = request.form['user']
        clean_user = user.strip("@")
        timeNow = time.asctime( time.localtime(time.time()) )
        page_link = "http://twitter.com/"+clean_user
        templateData = {
            'time': timeNow,
            'user': user,
            'page_link': page_link
        }
        return render_template('block.html', **templateData)

if __name__ == '__main__':
    app.run()
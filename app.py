from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from textblob import TextBlob
import time
from twikit import Client
from bs4 import BeautifulSoup
import json
import csv
import requests
from flask_cors import CORS
import serpapi
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)

# Load Twitter credentials from JSON file
with open('creds.json', 'r') as file:
    data = json.load(file)

# YouTube API
youtube = build('youtube', 'v3', developerKey='AIzaSyB3ssRXUCzlPiObIn0A8T0TTMGvRkRC1AA')

# Twitter Scraper
def get_free_proxies():
    url = 'https://www.proxysite.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    proxies = []
    for row in soup.find_all('tr')[1:]:
        data = row.find_all('td')
        proxy = {
            'ip': data[0].text,
            'port': data[1].text,
            'country': data[3].text,
            'https': data[6].text
        }
        proxies.append(proxy)
    return proxies


@app.route('/news', methods=['POST'])
def get_news():
    if request.method == 'POST':
        if 'query' in request.json:  # Assuming the request body is JSON
            query = request.json['query']
            params = {
                "engine": "google_news",
                "q": query,
                "gl": "in",
                "api_key": "e2a30aecb963d2caeb1fd6303c6c45ed641ec2df5a87afca772e7c0e63c37df7",
                "limit": 10  # Limiting to 10 rows
            }
            search = serpapi.search(params)
            results = []

            for dt in search['news_results']:
                if 'thumbnail' in dt.keys(): 
                    results.append({
                        'title': dt['title'],
                        'link': dt['link'],
                        'source_name': dt['source']['name'],
                        'source_icon': dt['source']['icon'],
                        'date': dt['date'],
                        'keywords': query,
                        'thumbnail': dt['thumbnail'],
                    })
                else :
                    results.append({
                        'title': dt['title'],
                        'link': dt['link'],
                        'source_name': dt['source']['name'],
                        'source_icon': dt['source']['icon'],
                        'date': dt['date'],
                        'thumbnail': 'none',
                        'keywords': query,
                    })
            
            return jsonify(results)


@app.route('/youtube', methods=['POST'])
def get_youtube():
    if request.method == 'POST':
        if 'video_id' in request.json:  # Assuming the request body is JSON
            video_id = request.json['video_id']
            request_comments = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText'
            )
            response = request_comments.execute()
            
            comments = []
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                author_profile_image = item['snippet']['topLevelComment']['snippet']['authorProfileImageUrl']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'published_at': comment['publishedAt'],
                    'likes': comment['likeCount'],
                    'profile_image': author_profile_image
                })
            
            return jsonify(comments)

# def get_sentiment(text):
#     template = """
#         #     text : {}
#         #     Berikan aku sentimen dari text diatas, jawaban hanya "positif" atau "negatif"
#         """
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         response_format={ "type": "json_object" },
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
#             {"role": "user", "content": template.format(text)}
#         ]
#     )
#     # print(response.choices[0].message.content)
#     resp = json.loads(response.choices[0].message.content)
#     return resp['sentiment']

# def get_sent_pers(text, perspektif):
#     template = """
#         #     dari teks ini: {}
#         #     deteksi apakah searah atau bertentangan dengan kebijakan ini : {}, 
#         #     jawaban hanya 1 kata : "positif", "negatif" atau "netral"
#         #     "positif" bila searah dan "negatif" bila bertentangan
#         """
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         response_format={ "type": "json_object" },
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
#             {"role": "user", "content": template.format(text, perspektif)}
#         ]
#     )
#     # print(response.choices[0].message.content)
#     resp = json.loads(response.choices[0].message.content)
#     return resp['jawaban']


def get_conclusion():
    return "Conclusion"

# def get_topic(lis):
#     template = """
#     #     {}
#     #
#     #     dari list komentar diatas, berikan aku 3 trending topiknya (buat hanya bentuk 2 kata) ouput yang diharapkan
#     #    {{
#     #      1: topik1
#     #      2: topik2
#     #      3: topik3
#     #    }}
#     """
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         response_format={ "type": "json_object" },
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
#             {"role": "user", "content": template.format(str(lis))}
#         ]
#     )
#     return json.loads(response.choices[0].message.content)



@app.route('/api/youtube/comments', methods=['POST'])
def youtube_comments():
    if request.method == 'POST':
        if 'hashtag' in request.json:  # Assuming the request body is JSON
            hashtag = request.json['hashtag']
            perspektif = request.json['perspektif']
            search_response = youtube.search().list(
                q=hashtag,
                part='snippet',
                type='video',
                maxResults=60  # You can adjust the number of results
            ).execute()

            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                # description = item['snippet']['description']
                # channelTitle = item['snippet']['channelTitle']
                # thumbnails = item['snippet']['thumbnails']['default']['url']
                # date = item['snippet']['publishTime']
                videos.append({
                    'video_id': video_id, 
                    'title': video_title, 
                    # 'description': description,
                    # 'channelTitle': channelTitle,
                    # 'thumbnails' : thumbnails,
                    # 'date' : date,
                })
            
            comments = []
            comment_count = 0
            for video in videos:
                request_comments = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video['video_id'],
                    textFormat='plainText'
                ).execute()

                for item in request_comments.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    author_profile_image = item['snippet']['topLevelComment']['snippet']['authorProfileImageUrl']
                    if comment_count <= 117:
                        if perspektif == '':
                            comments.append({
                                'author': comment['authorDisplayName'],
                                'text': comment['textDisplay'],
                                'published_at': comment['publishedAt'],
                                'likes': comment['likeCount'],
                                'profile_image': author_profile_image,
                                # 'sentiment': get_sentiment(comment['textDisplay'])
                                'sentiment': "positif"
                            })
                        else :
                            comments.append({
                                'author': comment['authorDisplayName'],
                                'text': comment['textDisplay'],
                                'published_at': comment['publishedAt'],
                                'likes': comment['likeCount'],
                                'profile_image': author_profile_image,
                                # 'sentiment': get_sent_pers(comment['textDisplay'], perspektif)
                                'sentiment': "positif"
                            })
                    else:
                        if perspektif == '':
                            comments.append({
                                'author': comment['authorDisplayName'],
                                'text': comment['textDisplay'],
                                'published_at': comment['publishedAt'],
                                'likes': comment['likeCount'],
                                'profile_image': author_profile_image,
                                # 'sentiment': get_sentiment(comment['textDisplay'])
                                'sentiment': "negatif"
                            })
                        else :
                            comments.append({
                                'author': comment['authorDisplayName'],
                                'text': comment['textDisplay'],
                                'published_at': comment['publishedAt'],
                                'likes': comment['likeCount'],
                                'profile_image': author_profile_image,
                                # 'sentiment': get_sent_pers(comment['textDisplay'], perspektif)
                                'sentiment': "negatif"
                            })

                    comment_count += 1
                    if comment_count >= 400:
                        break
                if comment_count >= 400:
                    break
            
            lis_comments = []
            for i in range(len(comments)):
                lis_comments.append(comments[i]['text'])
            
            result_data = {
                "comments": comments,
                # "topics": get_topic(lis_comments),
            }

            return jsonify(result_data)

# @app.route('/twitter', methods=['POST'])
# def twitter_api():
#     if request.method == 'POST':
#         if 'keyword' in request.json:
#             keyword = request.json['keyword']
#             client = Client('en-US')
#             client.login(auth_info_1=data['username'], password=data['password'])
            
#             twit = []
#             tweets = client.search_tweet(query=keyword, product='Latest')[:200]
            
#             for tweet in tweets:
#                 if tweet.user.followers_count < 5:
#                     continue
                
#                 _media = []
#                 _link = []
#                 content = tweet.full_text
#                 _id = tweet.id
#                 url = tweet.urls
                
#                 if tweet.urls:
#                     for link in tweet.urls:
#                         _link.append(link)
                
#                 if tweet.media:
#                     for i, media in enumerate(tweet.media):
#                         media_url = media.get('media_url_https')
#                         extension = media_url.rsplit('.', 1)[-1]
                        
#                         response = client.get_media(media_url)
#                         with open(f'media_download/media{tweet.id}_{i}.{extension}', 'wb') as fs:
#                             fs.write(response)
                        
#                         _media.append(media_url)
            
#                 _temp = {'ID': _id, 'Text': content, 'URL': _link, 'Media': _media, 'Created At': tweet.created_at}
#                 twit.append(_temp)
            
#             client.logout()
#             return jsonify(twit)


@app.route('/twitter', methods=['POST'])
def twitter_api():
    if request.method == 'POST':
        if 'keyword' in request.json:
            keyword = request.form['keyword']
            client = Client('en-US')
            client.login(auth_info_1=data['username'], password=data['password'])
            
            twit = []
            tweets = client.search_tweet(query=keyword, product='Latest')[:200]
            
            for tweet in tweets:
                if tweet.user.followers_count < 5:
                    continue
                
                _media = []
                _link = []
                content = tweet.full_text
                _id = tweet.id
                url = tweet.urls
                
                if tweet.urls:
                    for link in tweet.urls:
                        _link.append(link)
                
                if tweet.media:
                    for i, media in enumerate(tweet.media):
                        media_url = media.get('media_url_https')
                        extension = media_url.rsplit('.', 1)[-1]
                        
                        response = client.get_media(media_url)
                        with open(f'media_download/media{tweet.id}_{i}.{extension}', 'wb') as fs:
                            fs.write(response)
                        
                        _media.append(media_url)
            
                _temp = {'ID': _id, 'Text': content, 'URL': _link, 'Media': _media, 'Created At': tweet.created_at}
                twit.append(_temp)
            
            client.logout()
            return jsonify(twit)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'keyword' in request.form:  # Twitter Scraper
            keyword = request.form['keyword']
            client = Client('en-US')
            client.login(auth_info_1=data['username'], password=data['password'])
            
            twit = []
            tweets = client.search_tweet(query=keyword, product='Latest')[:200]
            
            for tweet in tweets:
                if tweet.user.followers_count < 5:  # Check if followers less than 5
                    continue  # Skip this tweet
                
                _media = []
                _link = []
                content = tweet.full_text
                _id = tweet.id
                url = tweet.urls
                created_at = tweet.created_at
                
                if tweet.urls:
                    for link in tweet.urls:
                        _link.append(link)
                
                if tweet.media:
                    for i, media in enumerate(tweet.media):
                        media_url = media.get('media_url_https')
                        extension = media_url.rsplit('.', 1)[-1]
                        
                        response = client.get_media(media_url)
                        with open(f'media_download/media{tweet.id}_{i}.{extension}', 'wb') as fs:
                            fs.write(response)
                        
                        _media.append(media_url)
            
                _temp = [_id, content, url, _media, created_at]
                twit.append(_temp)
            
            csv_file_path = 'twitter_data.csv'
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['ID', 'Text', 'URL', 'Media', 'Created At'])
                writer.writerows(twit)
            
            client.logout()
            return render_template('twitter_results.html', twit=twit)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

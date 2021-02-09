import pandas as pd
import numpy as np
from collections import Counter
import re
import itertools
import os
import io
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import string
import emoji
from bs4 import BeautifulSoup
import requests
import spacy
from first import preprocessing

nlp = spacy.load("en_core_web_sm-3.0.0")
tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')
nltk.download('stopwords')
stop = stopwords.words('english')
# print(len(stop))
stop = set(stop)
stop.add("The")
stop.add("It")
stop.add("My")
stop.add("'s")
stop.add("I")
stop.add(".<br")
stop.add("<br")
stop.add("br")
stop.add("/>")
stop.add("/><br")
stop.add("'t")
stop.add("'ve")
stop.add("use")
stop.add("one")
stop.add("br")
stop.add("This")
stop.add("They")
# print(len(stop))
punc = string.punctuation
porter_stemmer = PorterStemmer()


def preprocessing_article(article):
    article = str(article)
    # article = preprocessing(article)
    text_token = tokenizer.tokenize(article)
    text_token_stop = [token for token in text_token if not token in stop]
    text_token_stop_punt = [token for token in text_token_stop if not token in punc]
    # final_token = [porter_stemmer.stem(item) for item in text_token_stop_punt]
    return text_token_stop_punt


def url_to_string(url_site):
    res = requests.get(url_site)
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style", 'aside']):
        script.extract()
    return " ".join(re.split(r'[\n\t]+', soup.get_text()))


def create_corpora(url_list):
    article_list = []
    corpora = []

    for url in url_list:
        ny_bb = url_to_string(url)
        article_list.append(nlp(ny_bb))
        corpora.extend(nlp(ny_bb))
    return article_list, corpora


def write_file(filename, token_list):
    file_nba = open(filename, "w", encoding='utf-8')
    for final_token in token_list:
        iterator = itertools.chain(final_token)
        for item in iterator:
            file_nba.write(item + " ")

    file_nba.close()


def token_corpora(article_list):
    final_token_list = []
    for article in article_list:
        final_token_list.append(preprocessing_article(article))
    return final_token_list


url_list_nba = ["https://en.wikipedia.org/wiki/Boston_Celtics",
                "https://it.wikipedia.org/wiki/Brooklyn_Nets",
                "https://it.wikipedia.org/wiki/New_York_Knicks",
                "https://it.wikipedia.org/wiki/Chicago_Bulls",
                "https://it.wikipedia.org/wiki/Cleveland_Cavaliers",
                "https://it.wikipedia.org/wiki/Miami_Heat",
                "https://it.wikipedia.org/wiki/Minnesota_Timberwolves",
                "https://it.wikipedia.org/wiki/Oklahoma_City_Thunder",
                "https://it.wikipedia.org/wiki/Golden_State_Warriors",
                "https://it.wikipedia.org/wiki/Los_Angeles_Lakers",
                "https://it.wikipedia.org/wiki/Dallas_Mavericks",
                "https://it.wikipedia.org/wiki/Houston_Rockets",
                "https://it.wikipedia.org/wiki/San_Antonio_Spurs",
                "https://www.nba.com/celtics/history/recaps-2010s",
                "https://sports-statistics.com/nba/mavs-set-new-first-half-point-difference-record-nba/",
                "https://sports-statistics.com/nba/bucks-break-houston-rockets-record-for-most-3-pointers-in-a-game/",
                "https://www.ducksters.com/sports/basketballrules.php",
                "https://www.breakthroughbasketball.com/basics/basics.html",
                "https://en.wikipedia.org/wiki/Rules_of_basketball",
                "https://www.rulesofsport.com/sports/basketball.html",
                "https://www.fiba.basketball/basic-rules",
                "https://official.nba.com/rule-no-1-court-dimensions-equipment/",
                "https://official.nba.com/rule-no-2-duties-of-the-officials/",
                "https://official.nba.com/rule-no-3-duties-of-the-officials/",
                "https://official.nba.com/rule-no-3-players-substitutes-and-coaches/",
                "https://official.nba.com/rule-no-4-definitions/",
                "https://official.nba.com/rule-no-5-scoring-and-timing/",
                "https://official.nba.com/rule-no-6-putting-ball-in-play-live-dead-ball/",
                "https://official.nba.com/rule-no-7-24-second-clock/",
                "https://official.nba.com/rule-no-8-out-of-bounds-and-throw-in/",
                "https://official.nba.com/rule-no-9-free-throws-and-penalties/",
                "https://official.nba.com/rule-no-10-violations-and-penalties/",
                "https://official.nba.com/rule-no-11-basket-interference-goaltending/",
                "https://official.nba.com/rule-no-12-fouls-and-penalties/",
                "https://official.nba.com/rule-no-13-instant-replay/",
                "https://official.nba.com/rule-no-14-coaches-challenge/",
                ]

url_list_soccer = ["https://en.wikipedia.org/wiki/2019%E2%80%9320_Bundesliga",
                   "https://en.wikipedia.org/wiki/2019%E2%80%9320_Serie_A",
                   "https://en.wikipedia.org/wiki/2019%E2%80%9320_Premier_League",
                   "https://en.wikipedia.org/wiki/UEFA_Champions_League",
                   "https://en.wikipedia.org/wiki/Serie_A",
                   "https://en.wikipedia.org/wiki/La_Liga",
                   "https://en.wikipedia.org/wiki/Bundesliga",
                   "https://en.wikipedia.org/wiki/Premier_League",
                   "https://en.wikipedia.org/wiki/Association_football",
                   "https://www.rulesofsport.com/sports/football.html"]

article_list_NBA, corpora_NBA = create_corpora(url_list_nba)
print("lunghezza lista di articoli NBA: ", len(article_list_NBA))
print("lunghezza corpora_NBA: ", len(corpora_NBA))
nba_token_corpora = token_corpora(article_list_NBA)

article_list_soccer, corpora_soccer = create_corpora(url_list_soccer)
print("lunghezza lista di articoli soccer: ", len(article_list_soccer))
print("lunghezza corpora_soccer: ", len(corpora_soccer))
soccer_token_corpora = token_corpora(article_list_soccer)

# create file
filename = input("insert filename for NBA corpus")
write_file(filename, nba_token_corpora)

filename = input("insert filename for soccer corpus")
write_file(filename, soccer_token_corpora)

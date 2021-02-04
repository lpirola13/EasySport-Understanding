import re
import time
from datetime import datetime
import emoji
import spacy
from psaw import PushshiftAPI
import praw
import datetime

from spacy_langdetect import LanguageDetector


def preprocessing(text):
    # Rimuovo i newline
    text = text.replace("\n", "")
    # Rimuovo i link
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    # Sostituisco le emoji con i loro aliases
    text = emoji.demojize(text)
    # Rimuovo i due punti prima e dopo dell'alias
    text = re.sub(r'(:)(.*?)(:)', r' \2 ', text)
    # Rimuovo l'underscore se gli alias sono composti da più parole
    text = re.sub(r'(_)', ' ', text)
    # Rimuovo |
    text = text.replace('|', '')
    # Rimuovo le parentesi () dal testo
    text = re.sub(r'(\()([^)]+)(\))', '\g<2>', text)
    # Rimuovo i numeri dal testo
    text = re.sub(r'(?<![a-zA-Z]-)(\b\d+\b)', ' ', text)
    # Rimuovo [Video]
    text = text.replace(']', '] ')
    # Rimuovo [HIGHLIGHT]
    text = text.replace('[HIGHLIGHT] ', '')
    # Rimuovo [highlight]
    text = text.replace('[highlight] ', '')
    # Rimuovo [Highlight]
    text = text.replace('[Highlight] ', '')
    # Rimuovo (Highlight)
    text = text.replace('(Highlight) ', '')
    # Rimuovo [Highlights]
    text = text.replace('[Highlights] ', '')
    # Rimuovo [Highlight Request]
    text = text.replace('[Highlight Request] ', '')
    # Rimuovo [OC]
    text = text.replace('[OC] ', '')
    # Rimuovo OG
    text = text.replace('OG ', '')
    # Rimuovo [Serious]
    text = text.replace('[Serious] ', '')
    # Rimuovo [serious]
    text = text.replace('[serious] ', '')
    # Rimuovo (serious)
    text = text.replace('(serious) ', '')
    # Rimuovo [Post Game Thread]
    text = text.replace('[Post Game Thread] ', '')
    # Rimuovo [Post-Game Thread]
    text = text.replace('[Post-Game Thread] ', '')
    # Rimuovo GAME THREAD
    text = text.replace('GAME THREAD: ', '')
    # Rimuovo [GAME THREAD]
    text = text.replace('[GAME THREAD] ', '')
    # Rimuovo [Game Thread]
    text = text.replace('[Game Thread] ', '')
    # Rimuovo Daily Discussion
    text = text.replace('Daily Discussion', '')
    # Rimuovo [Discussion]
    text = text.replace('[Discussion] ', '')
    # Rimuovo (Discussion)
    text = text.replace('(Discussion) ', '')
    # Rimuovo [Discussions]
    text = text.replace('[Discussions] ', '')
    # Rimuovo [Discussion Thread]
    text = text.replace('[Discussion Thread] ', '')
    # Rimuovo [Question]
    text = text.replace('[Question] ', '')
    # Rimuovo [Clip Request]
    text = text.replace('[Clip Request] ', '')
    # Rimuovo [Video Request]
    text = text.replace('[Video Request] ', '')
    # Rimuovo [video request]
    text = text.replace('[video request] ', '')
    # Rimuovo [REQUEST]
    text = text.replace('[REQUEST] ', '')
    # Rimuovo [SERIOUS NEXT DAY THREAD]
    text = text.replace('[SERIOUS NEXT DAY THREAD] ', '')
    # Rimuovo BREAKING:
    text = text.replace('BREAKING: ', '')
    # Rimuovo [Match Thread]
    text = text.replace('[Match Thread] ', '')
    # Rimuovo Post Match Thread:
    text = text.replace('Post-Match Thread: ', '')
    # Rimuovo Post Match Thread:
    text = text.replace('Post Match Thread: ', '')
    # Rimuovo Post Match Thread:
    text = text.replace('Post Match Thread ', '')
    # Rimuovo Match Thread:
    text = text.replace('Match Thread: ', '')
    # Rimuovo Match Thread
    text = text.replace('Match Thread ', '')
    # Rimuovo [Pre Match Thread]
    text = text.replace('[Pre Match Thread] ', '')
    # Rimuovo [Post Match Thread]
    text = text.replace('[Post Match Thread] ', '')
    # Rimuovo Post-Match Thread:
    text = text.replace('[Post-Match Thread:] ', '')
    # Rimuovo Free Talk Friday
    text = text.replace('Free Talk Friday', '')
    # Rimuovo [Video]
    text = text.replace('[Video] ', '')
    # Rimuovo Video
    text = text.replace('VIDEO ', '')
    # Rimuovo +
    text = text.replace('+', '')
    # Rimuovo i doppi spazi
    text = re.sub(r' {2,}', ' ', text)
    tokens = [token for token in nlp(text) if not token.is_punct]
    text = " ".join(str(token) for token in tokens)
    return text


def start_scraping(subreddit, months, filename):
    today = datetime.date.today()
    after = today.replace(day=1)
    total = 0
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(0, months):
            before = after
            after = after - datetime.timedelta(days=5)
            after = after.replace(day=1)
            print("before: {} after: {}".format(before, after))
            after_week = before
            week = 1
            while after_week > after:
                temp = after_week
                after_week = after_week - datetime.timedelta(days=7)
                if after_week < after:
                    after_week = after
                print("\tweek {} - before: {} after: {}".format(week, temp, after_week))
                week = week + 1
                # Recupero i post più importanti della settimana e li ordino in maniera decrescente in base al numero
                # di commenti
                for count, submission in enumerate(api.search_submissions(subreddit=subreddit,
                                                                          before=temp,
                                                                          sort_type="num_comments",
                                                                          sort="desc",
                                                                          after=after_week,
                                                                          fields=["id", "title", "created_utc"])):
                    # Rimuovo i simboli non necessari
                    text = preprocessing(submission.title)
                    date = str(datetime.datetime.fromtimestamp(submission.created_utc))[0:10]
                    #print("\t\t{} - {} - {}".format(count, date, submission.title))
                    print("\t\t{} - {} - {}".format(count, date, text))
                    f.write(text + "\n")
                total = total + count
                print("\ttotal submissions: {}".format(total))
                time.sleep(10)


if __name__ == '__main__':
    months = 12
    subreddit = 'nba'
    filename = 'corpus-basketball.txt'
    reddit = praw.Reddit(
        client_id="wizInGr3eHuuGw",
        client_secret="s_8X-6HGNwNFTpOaAqnytIV1NMuxzw",
        user_agent="User-Agent: easysport-understanding:v1.0.0 (by /u/lorenzopirola44)"
    )
    api = PushshiftAPI(reddit)
    nlp = spacy.load("en_core_web_sm")
    start_scraping(subreddit, months, filename)

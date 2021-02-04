
import praw
from datetime import datetime
import sparql #INSTALL sparql-client
import spotlight #INSTALL pyspotlight
import emoji
import re
import time
from Entity import Entity
import argparse
import requests
s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')


def get_info(submission):
    text = submission.title.replace("\n", "")
    text = re.sub(r'http\S+', '', text)
    text = text.encode('ascii', 'ignore').decode()
    return text, str(datetime.fromtimestamp(submission.created_utc))[:-9]


def demojize(text):
    text = emoji.demojize(text)
    text = re.sub(r'(:)(.*?)(:)', r' \2 ', text)
    text = re.sub(r'(_)', ' ', text)
    return text


def annotate(text):
    annotations_list = []
    try:
        annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', text, confidence=0.2)
        time.sleep(0.2)
        for annotation in annotations:
            statement = ('select ?name where {<' + annotation[
                'URI'] + '> foaf:name ?name. FILTER (lang(?name) = "en") } ORDER BY DESC(strlen(str(?name))) LIMIT 1')
            result = s.query(query=statement)
            time.sleep(0.2)
            name = annotation['surfaceForm']
            if result:
                for row in result.fetchone():
                    values = sparql.unpack_row(row)
                    name = values[0]
            annotations_list.append(name)
            type = annotation['types'].rsplit(',', 1)[-1]
            type = type.rsplit(':', 1)[-1]
            if type:
                entity = Entity(url=annotation['URI'], name=name, type=type)
            else:
                entity = Entity(url=annotation['URI'], name=name)
            entity.meta.id = annotation['URI']
            entity.save()
            text = text.replace(annotation['surfaceForm'], annotation['URI'])
        return text, annotations_list
    except spotlight.SpotlightException:
        return text, annotations_list
    except requests.exceptions.HTTPError as error:
        print(error)
        return text, annotations_list


def main(subreddit, limit):
    Entity.init()
    reddit = praw.Reddit(
        client_id="wizInGr3eHuuGw",
        client_secret="s_8X-6HGNwNFTpOaAqnytIV1NMuxzw",
        user_agent="User-Agent: easysport-understanding:v1.0.0 (by /u/lorenzopirola44)"
    )
    with open("corpus-reddit.txt", 'w', encoding='utf-8') as f:
        for count, submission in enumerate(reddit.subreddit(subreddit).top(time_filter="year", limit=limit), 1):
            start_time = time.time()
            text, date = get_info(submission)
            text = demojize(text)
            text, annotations_list = annotate(text)
            print(text)
            elapsed=time.time()-start_time
            print("{} - elapsed: {}  date: {}  entities: {} \n\t\tannotations: {}".format(count, round(elapsed,2), date, len(annotations_list),
                                                                                    annotations_list))
            f.write(text+"\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download submission from subreddit')
    parser.add_argument('--subreddit', required=True, help='subreddit')
    parser.add_argument('--limit', required=True, help='number of submission to download')
    args = parser.parse_args()
    print("subreddit: {} limit: {}".format(args.subreddit, args.limit))
    main(subreddit=args.subreddit, limit=int(args.limit))
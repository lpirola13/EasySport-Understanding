import sparql
from TwitterAPI import TwitterAPI, TwitterPager
import spotlight
import emoji
import re
import time
from Entity import Entity
import argparse
import requests
s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')


def get_tweet_id_text(item):
    text = item['text'].replace("\n", " ")
    for mention in item['entities']['user_mentions']:
        text = text.replace('@' + mention['screen_name'], mention['name'])
    text = re.sub(r'http\S+', '', text)
    text = text.encode('ascii', 'ignore').decode()
    return text, item['created_at'][:10]


def demojize(text):
    text = emoji.demojize(text)
    text = re.sub(r'(:)(.*?)(:)', r' \2 ', text)
    text = re.sub(r'(_)', ' ', text)
    return text


def annotate(text):
    annotations_list = []
    try:
        annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', text, confidence=0.8)
        for annotation in annotations:
            statement = ('select ?name where {<' + annotation[
                'URI'] + '> foaf:name ?name. FILTER (lang(?name) = "en") } ORDER BY DESC(strlen(str(?name))) LIMIT 1')
            result = s.query(query=statement)
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


def main(screen_name, limit):
    consumer_key = '5XKP99E6alrqmG97hRpqqB9dm'
    consumer_secret = 'Dy9FE4jhZ8mkACUvaoMVRuRrtPKxkjwDCNlseC1wRBBhxqtgAs'
    access_token_key = '1332264202069807105-ZWZx7SGTzoGoZTrtoq9v22FRbBvJOd'
    access_token_secret = 'D9rQhOijHmLUGCesSiDJV9Bklbt0wA4yuEnyG72ppoc3D'
    Entity.init()
    api = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret)
    with open("corpus.txt", 'w', encoding='utf-8') as f:
        pager = TwitterPager(api, 'statuses/user_timeline', {'screen_name': screen_name,
                                                             'exclude_replies': 'true',
                                                             'include_rts': 'false',
                                                             'count': 10})
        count = 1
        for item in pager.get_iterator(wait=1):
            if count%10==0:
                time.sleep(10)
            if count == limit:
                break
            start_time = time.time()
            text, date = get_tweet_id_text(item)
            text = demojize(text)
            print(text)
            text, annotations_list = annotate(text)
            print(text)
            elapsed = time.time() - start_time
            print("{} - elapsed: {}  date: {}  entities: {} \n\t\tannotations: {}".format(count, round(elapsed,2), date, len(annotations_list),
                                                                                    annotations_list))
            f.write(text+"\n")
            count = count + 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download tweets from Twitter user')
    parser.add_argument('--screen_name', required=True, help='screen name')
    parser.add_argument('--limit', required=True, help='number of tweets to download')
    args = parser.parse_args()
    print("user: {} limit: {}".format(args.screen_name, args.limit))
    main(screen_name=args.screen_name, limit=args.limit)

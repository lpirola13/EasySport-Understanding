from urllib.parse import unquote

from BasketballEntity import BasketballEntity
from dandelion import DataTXT, DandelionException
from datetime import datetime
import emoji
import praw
import re
import requests
from SoccerEntity import SoccerEntity
import spacy
from spacy.lang.char_classes import LIST_ELLIPSES, ALPHA_UPPER, CONCAT_QUOTES, ALPHA, LIST_ICONS, ALPHA_LOWER
from spacy.util import compile_infix_regex
import sparql
import spotlight
import time

nlp = spacy.load("en_core_web_sm-3.0.0")
datatxt = DataTXT(token='67fae4be6482439894e8759a9eb87b45')

infixes = (
        LIST_ELLIPSES
        + LIST_ICONS
        + [
            r"(?<=[0-9])[+\*^](?=[0-9-])",
            r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(
                al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
            ),
            r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
            r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
        ]
)

infix_re = compile_infix_regex(infixes)
nlp.tokenizer.infix_finditer = infix_re.finditer

prefixes = list(nlp.Defaults.prefixes)
prefixes.remove('\\(')
prefix_regex = spacy.util.compile_prefix_regex(prefixes)
nlp.tokenizer.prefix_search = prefix_regex.search

suffixes = list(nlp.Defaults.suffixes)
suffixes.remove('\\)')
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search


s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')


def get_text(submission):
    # Rimuovo i newline
    text = submission.title.replace("\n", "")
    # Rimuovo i link
    text = re.sub(r'http\S+', '', text)
    # Rimuovo i caratteri non ascii
    text = text.encode('ascii', 'ignore').decode()
    # Rimuovo i risultati
    text = re.sub(r"(0|[1-9]\d*)-(0|[1-9]\d*)", '', text)
    return text, str(datetime.fromtimestamp(submission.created_utc))[:-9]


def demojize(text):
    # Sostituisco emoji con i loro alias
    text = emoji.demojize(text)
    # Rimuovo i due punti prima e dopo dell'alias
    text = re.sub(r'(:)(.*?)(:)', r' \2 ', text)
    # Rimuovo l'underscore se gli alias sono composti da più parole
    text = re.sub(r'(_)', ' ', text)
    return text


# def annotate(text, sport):
#     # Annotazione con Dandelion
#     try:
#         response = datatxt.nex(text, include=["types", "lod"])
#         time.sleep(0.2)
#         for annotation in response.annotations:
#             print(annotation)
#             # Sostituisco i nomi delle entità identificate nel testo
#             text = text.replace(annotation['spot'], annotation['title'])
#     except DandelionException as error:
#         print(error)
#     print("DANDELION: {}".format(text))
#     annotations_list = []
#     # Annotazione con DBpedia
#     try:
#         annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', text, confidence=0.8)
#         time.sleep(0.2)
#         for annotation in annotations:
#             # Ricerca nome e abstract su DBpedia a partire dall'URI identificato
#             statement = ('select ?name ?abstract where {<' + annotation['URI'] + '> foaf:name ?name. <' + annotation[
#                 'URI'] + '> dbo:abstract ?abstract FILTER (lang(?name) = "en" && lang(?abstract) = "en" ) } ORDER BY '
#                          'DESC(strlen(str(?name))) LIMIT 1')
#             result = s.query(query=statement)
#             time.sleep(0.2)
#             name = annotation['surfaceForm']
#             abstract = ""
#             if result:
#                 for row in result.fetchone():
#                     values = sparql.unpack_row(row)
#                     name = values[0]
#                     abstract = str(next(nlp(values[1]).sents))
#             # Come URI mantengo solo l'ultima parte (in lowercase) dell'URI originale
#             uri = annotation['URI'].rsplit('/', 1)[-1].lower()
#             # Come type mantengo solo l'ultimo livello nella gerarchia. Converto in stringa normale da CamelCase
#             type = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", annotation['types'].rsplit(',', 1)[-1].rsplit(':', 1)[-1])
#             if type:
#                 annotations_list.append(name + ":" + type)
#             else:
#                 annotations_list.append(name)
#             # Memorizzo l'entità identificata nel DB
#             persist(sport, uri, name, abstract, type)
#             # Sostituisco l'URI dell'entità nel testo
#             text = text.replace(annotation['surfaceForm'], uri)
#     except spotlight.SpotlightException:
#         pass
#     except requests.exceptions.HTTPError as error:
#         print(error)
#         return None
#     finally:
#         print("DBPEDIA:   {}".format(text))
#         # Tokenization del testo e rimozione stop words e punctuation
#         tokens = [token for token in nlp(text.lower()) if not token.is_stop and not token.is_punct]
#         text = " ".join(str(token) for token in tokens)
#         print("FINAL:     {}".format(text))
#         return text, annotations_list


def annotate(text, sport):
    text = text.lower()
    # Annotazione con Dandelion
    annotations_list = []
    try:
        response = datatxt.nex(text, min_confidence=0.65, include=["types", "lod"])
        time.sleep(0.2)
        for annotation in response.annotations:
            uri =  unquote(annotation['lod']['dbpedia'])
            name = annotation['title']
            abstract = ""
            # Ricerca nome e abstract su DBpedia a partire dall'URI identificato
            statement = ('select ?name ?abstract where {<' + uri + '> foaf:name ?name. <' + uri + '> dbo:abstract '
                                                                                                  '?abstract FILTER ('
                                                                                                  'lang(?name) = "en" '
                                                                                                  '&& lang('
                                                                                                  '?abstract)= "en" )} '
                                                                                                  'ORDER BY DESC('
                                                                                                  'strlen(str( '
                                                                                                  '?name))) LIMIT 1')
            result = s.query(query=statement)
            time.sleep(0.2)
            if result:
                abstract = ""
                for row in result.fetchone():
                    values = sparql.unpack_row(row)
                    name = values[0]
                    abstract = str(next(nlp(values[1]).sents))
            # Come URI mantengo solo l'ultima parte (in lowercase) dell'URI originale
            uri = uri.rsplit('/', 1)[-1].lower()
            # Come type mantengo solo l'ultimo livello nella gerarchia. Converto in stringa normale da CamelCase
            if len(annotation['types']) > 0:
                type = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", annotation['types'][0].rsplit('/', 1)[-1])
                annotations_list.append(name + ":" + type)
            else:
                type = ""
                annotations_list.append(name)
            # Memorizzo l'entità identificata nel DB
            persist(sport, uri, name, abstract, type)
            # Sostituisco l'URI dell'entità nel testo
            text = text.replace(annotation['spot'], uri)
    except DandelionException as error:
        print(error)
    finally:
        print("DANDELION: {}".format(text))
        # Tokenization del testo e rimozione stop words e punctuation
        tokens = [token for token in nlp(text.lower()) if not token.is_stop and not token.is_punct]
        text = " ".join(str(token) for token in tokens)
        print("FINAL:     {}".format(text))
        return text, annotations_list


def persist(sport, uri, name, abstract, type):
    entity = None
    if sport == "soccer":
        if type:
            entity = SoccerEntity(name=name, abstract=abstract, type=type)
        else:
            entity = SoccerEntity(name=name, abstract=abstract)
    elif sport == "basketball":
        if type:
            entity = BasketballEntity(name=name, abstract=abstract, type=type)
        else:
            entity = BasketballEntity(name=name, abstract=abstract)
    entity.meta.id = uri
    entity.save()


def main(sport, subreddit, limit):
    if sport == "basketball":
        BasketballEntity.init()
    elif sport == "soccer":
        SoccerEntity.init()
    reddit = praw.Reddit(
        client_id="wizInGr3eHuuGw",
        client_secret="s_8X-6HGNwNFTpOaAqnytIV1NMuxzw",
        user_agent="User-Agent: easysport-understanding:v1.0.0 (by /u/lorenzopirola44)"
    )
    with open("corpus-" + sport + ".txt", 'w', encoding='utf-8') as f:
        for count, submission in enumerate(reddit.subreddit(subreddit).top(time_filter="year", limit=limit), 1):
            start_time = time.time()
            text, date = get_text(submission)
            text = demojize(text)
            print("\n{}".format(count))
            print("ORIGINAL:  {}".format(text))
            text, annotations_list = annotate(text, sport)
            elapsed = time.time() - start_time
            print("elapsed: {}  date: {}  entities: {} \n\t\tannotations: {}".format(round(elapsed, 2), date,
                                                                                     len(annotations_list),
                                                                                     annotations_list))
            f.write(text + "\n")


if __name__ == '__main__':
    sport = "basketball"
    subreddit = 'nba'
    limit = 2
    main(sport, subreddit, limit)

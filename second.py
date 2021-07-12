import re
import time
from urllib.parse import unquote

import requests
import spacy
import sparql
import spotlight
from dandelion import DataTXT, DandelionException
from spacy.lang.char_classes import LIST_ELLIPSES, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, LIST_ICONS, ALPHA, HYPHENS
from spacy.util import compile_infix_regex
from BasketballEntity import BasketballEntity
from SoccerEntity import SoccerEntity

import nltk
from nltk.stem import WordNetLemmatizer


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


def query_dbpedia(uri):
    statement = ('select ?name ?abstract where {'
                 'OPTIONAL {<' + uri + '> foaf:name ?name.}.'
                                       'OPTIONAL {<' + uri + '> dbo:abstract ?abstract.}.'
                                                             'FILTER (lang(?name) = "en" && lang(?abstract)= "en" )} '
                                                             'ORDER BY DESC(strlen(str(?name))) LIMIT 1')
    result = s.query(query=statement)
    for row in result.fetchone():
        values = sparql.unpack_row(row)
        name = values[0]
        abstract = str(next(nlp(values[1]).sents))
        return name, abstract


def annotate_dbpedia(text, confidence, sport):
    annotations_list = []
    try:
        annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', text, confidence=confidence)
        for annotation in annotations:
            uri = annotation['URI']
            # Recupero il tipo più specifico (ultimo della lista) e converto da CamelCase a stringa normale
            type = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", annotation['types'].rsplit(',', 1)[-1].rsplit(':', 1)[-1])
            # Ricerca nome e abstract su DBpedia a partire dall'URI identificato
            try:
                name, abstract = query_dbpedia(uri)
                if not name:
                    # Se il nome non esisto uso l'identificativo dell'entità nel testo
                    name = annotation['surfaceForm']
                if not abstract:
                    # Se l'abstract non esiste lascio il campo vuoto
                    abstract = ""
            except (TypeError, requests.exceptions.HTTPError) as error:
                print("ERROR: {} {}".format(uri, error))
                name = annotation['surfaceForm']
                abstract = ""
            # Come URI mantengo solo l'ultima parte (in lowercase) dell'URI originale
            uri = uri.rsplit('/', 1)[-1]
            # Sostituisco l'URI dell'entità nel testo
            text = re.sub(r'\b%s\b' % (annotation['surfaceForm']), uri, text)
            if type:
                annotations_list.append(name + ":" + type)
            else:
                annotations_list.append(name)
            # Memorizzo l'entità identificata nel DB
            persist(sport, uri.lower(), name, abstract, type)
    except (spotlight.SpotlightException, requests.exceptions.HTTPError) as error:
        print("DBPEDIA ERROR: {}".format(error))
    return text, annotations_list


def annotate_dandelion(text, confidence, sport):
    annotations_list = []
    try:
        annotations = datatxt.nex(text, min_confidence=confidence, include=["types", "lod"]).annotations
        for annotation in annotations:
            # converto l'uri della risorsa in stringa
            uri = unquote(annotation['lod']['dbpedia'])
            type = None
            if len(annotation['types']) > 0:
                # Recupero il tipo più specifico (primo della lista) e converto da CamelCase a stringa normale
                type = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", annotation['types'][0].rsplit('/', 1)[-1])
            # Ricerca nome e abstract su DBpedia a partire dall'URI identificato
            try:
                name, abstract = query_dbpedia(uri)
                if not name:
                    # Se il nome non esisto uso il titolo ritornato da Dandelion
                    name = annotation['title']
                if not abstract:
                    # Se l'abstract non esiste lascio il campo vuoto
                    abstract = ""
            except (TypeError, requests.exceptions.HTTPError) as error:
                print("ERROR: {} {}".format(uri, error))
                name = annotation['title']
                abstract = ""
            # Come URI mantengo solo l'ultima parte (in lowercase) dell'URI originale
            uri = uri.rsplit('/', 1)[-1]
            # Sostituisco l'URI dell'entità identificata nel testo
            text = re.sub(r'\b%s\b' % (annotation['spot']), uri, text)
            if type:
                annotations_list.append(name + ":" + type)
            else:
                annotations_list.append(name)
            # Memorizzo l'entità identificata nel DB
            persist(sport, uri.lower(), name, abstract, type)
    except (DandelionException, requests.exceptions.HTTPError) as error:
        print("DANDELION ERROR: {}".format(error))
    return text, annotations_list


# def annotate(text, sport, method, confidence):
#     annotations = []
#     if method == 'dbpedia':
#         text, annotations = annotate_dbpedia(text, confidence, sport)
#     elif method == 'dandelion':
#         text, annotations = annotate_dandelion(text, confidence, sport)
#     # Tokenization del testo e rimozione stop words e punctuation
#     print("ANN:   {}".format(text), end='')
#     lemmas = [wnl.lemmatize(str(token)).lower() for token in nlp(text) if not token.is_stop and not token.is_punct]
#     tokens = [lemma for lemma in lemmas if len(str(lemma)) > 1]
#     text = " ".join(str(token) for token in tokens)
#     return text, annotations


def annotate(text, sport, method, confidence):
    annotations = []
    if method == 'dbpedia':
        text, annotations = annotate_dbpedia(text, confidence, sport)
    elif method == 'dandelion':
        text, annotations = annotate_dandelion(text, confidence, sport)
    # Tokenization del testo e rimozione stop words e punctuation
    tokens = [lemmatizer.lemmatize(str(token)) for token in nlp(text)]
    lemmatized_text = " ".join(token for token in tokens)
    print("ANN:       {}".format(text), end='')
    print("ANN-LEMMA: {}".format(lemmatized_text), end='')
    return text.lower(), lemmatized_text.lower(), annotations


def main(path_from, path_to, path_to_lemma, row_from, sport, confidence, count_dandelion):
    if sport == "basketball":
        BasketballEntity.init()
    elif sport == "soccer":
        SoccerEntity.init()
    with open(path_from, 'r', encoding="utf-8") as from_file, open(path_to, 'a', encoding="utf-8") as to_file, open(path_to_lemma, 'a', encoding="utf-8") as to_file_lemma:
        try:
            chunk = from_file.readlines()[row_from:50000]      # numero di righe che considera ogni volta
            for row in chunk:
                #if count_dandelion < 1000:
                print("ROW:       {}".format(row_from))
                print("TEXT:      {}".format(row), end='')
                # words = ['ball', 'crossbar', 'free kick', 'referee', 'card', 'striker', 'pitch',
                #          'wing', 'conference', 'ballon',
                #          'forward', 'winger', 'penalty', 'offside', 'goalkeeper', 'midfielder', 'defender', 'assist',
                #          'flagrant', 'ring', 'basket', 'block', 'guard', 'rebound', 'steal', 'conference', 'field']
                # if any(word in row.lower() for word in words):
                #    text, lemmatized_text, annotations = annotate(row, sport=sport, method='dandelion',
                #                                                  confidence=confidence)
                #    count_dandelion += 1
                # else:
                text, lemmatized_text, annotations = annotate(row, sport=sport, method='dbpedia', confidence=confidence)
                print("FINAL:     {}".format(text))
                print("\tANNOTATIONS: {}".format(annotations))
                #print("DANDELION REQUESTS: {}\n".format(count_dandelion))
                # print(text)
                to_file.write(text)
                # print(text)
                to_file_lemma.write(lemmatized_text)
                row_from += 1
                #else:
                    #print("LAST ROW: {}".format(row_from))
            exit(0)
        except KeyboardInterrupt:
            to_file.flush()
            to_file.close()
            to_file_lemma.flush()
            to_file_lemma.close()
            exit(0)


if __name__ == '__main__':
    path_from = input(f'input file: ')
    path_to = input(f'output file: ')
    path_to_lemma = input(f'output file lemma: ')
    row_from = input(f'row from: ') # 5320
    sport = input(f'sport: ')
    confidence = input(f'confidence: ')
    #count_dandelion = input(f'dandelion requests: ')
    #token = input(f'token: ')       
    datatxt = DataTXT(token='')
    count_dandelion = 0
    s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')
    nlp = spacy.load("en_core_web_sm")
    lemmatizer = WordNetLemmatizer()
    # Per evitare di splittare su (
    prefixes = list(nlp.Defaults.prefixes)
    prefixes.remove('\\(')
    prefix_regex = spacy.util.compile_prefix_regex(prefixes)
    nlp.tokenizer.prefix_search = prefix_regex.search
    # Per evitare di splittare su )
    suffixes = list(nlp.Defaults.suffixes)
    suffixes.remove('\\)')
    suffix_regex = spacy.util.compile_suffix_regex(suffixes)
    nlp.tokenizer.suffix_search = suffix_regex.search
    infixes = (
            LIST_ELLIPSES
            + LIST_ICONS
            + [
                # r"(?<=[0-9])[+\-\*^](?=[0-9-])",  Originale
                r"(?<=[0-9])[+\*^](?=[0-9-])",  # Modificata
                r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(
                    al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
                ),
                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                # r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>/=](?=[{a}])".format(a=ALPHA),
            ]
    )
    infix_re = compile_infix_regex(infixes)
    nlp.tokenizer.infix_finditer = infix_re.finditer
    main(str(path_from), str(path_to), str(path_to_lemma), int(row_from), str(sport), confidence, int(count_dandelion))

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
    time.sleep(0.1)
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
    except spotlight.SpotlightException as error:
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
    except DandelionException as error:
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
    print("ANN:   {}".format(text), end='')
    lemmas = [wnl.lemmatize(str(token)).lower() for token in nlp(text) if not token.is_stop and not token.is_punct]
    tokens = [lemma for lemma in lemmas if len(str(lemma)) > 1]
    text = " ".join(str(token) for token in tokens)
    return text, annotations


def main(path_from, path_to, row_from, row_to, sport, method, confidence):
    if sport == "basketball":
        BasketballEntity.init()
    elif sport == "soccer":
        SoccerEntity.init()
    with open(path_from, 'r') as from_file, open(path_to, 'a') as to_file:
        chunk = from_file.readlines()[row_from:row_to]
        for row in chunk:
            if len(row) > 2:
                print("ROW:   {}".format(row_from))
                print("TEXT:  {}".format(row), end='')
                text, annotations = annotate(row, sport=sport, method=method, confidence=confidence)
                print("FINAL: {}".format(text))
                print("\tANNOTATIONS: {}\n".format(annotations))
                to_file.write(text + '\n')
                row_from += 1


if __name__ == '__main__':
    path_from = 'corpus-soccer.txt'
    path_to = 'corpus-soccer-clean.txt'
    row_from = 0  # uguale al precedente
    row_to = 2000
    sport = 'basketball'
    method = 'dbpedia'
    confidence = 0.6
    datatxt = DataTXT(token='67fae4be6482439894e8759a9eb87b45')
    s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')
    nlp = spacy.load("en_core_web_sm")
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
    # Considera come unico token due parole unite da hypen
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
                r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>/=](?=[{a}])".format(a=ALPHA),
            ]
    )
    #nltk.download('wordnet')
    # Create WordNetLemmatizer object
    wnl = WordNetLemmatizer()
    infix_re = compile_infix_regex(infixes)
    nlp.tokenizer.infix_finditer = infix_re.finditer
    main(path_from, path_to, row_from, row_to, sport, method, confidence)

import re
import time
from urllib.parse import unquote

import emoji
import requests
import spacy
import sparql
import spotlight
from dandelion import DataTXT, DandelionException
from nltk import WordNetLemmatizer
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, ALPHA, HYPHENS
from spacy.util import compile_infix_regex

from BasketballEntity import BasketballEntity
from SoccerEntity import SoccerEntity


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
        annotations = spotlight.annotate('https://api.dbpedia-spotlight.org/en/annotate', text, confidence=confidence, support=100)
        for annotation in annotations:
            print(annotation)
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
            #persist(sport, uri.lower(), name, abstract, type)
    except spotlight.SpotlightException as error:
        print("DBPEDIA ERROR: {}".format(error))
    return text, annotations_list


def annotate_dandelion(text, confidence, sport):
    annotations_list = []
    try:
        annotations = datatxt.nex(text, min_confidence=confidence, include=["types", "lod"]).annotations
        for annotation in annotations:
            print(annotation)
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
            #persist(sport, uri.lower(), name, abstract, type)
    except DandelionException as error:
        print("DANDELION ERROR: {}".format(error))
    return text, annotations_list


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
SoccerEntity.init()

# offside, defender
# text = 'Dale Johnson via Twitter This is a law guidance clip used by FIFA UEFA some years ago to illustrate that situations like this are OFFSIDE OFFENCES as the ball is not played to the attacker but the attacker comes from to challenge the defender very shortly'

# goalkeeper
# text = "IIFHS The World 's Best Man Goalkeeper Of the Decade Manuel Neuer"

# ball
# text = "All Messi goals for Barcelona and where he FIRST touched the ball visualisation"

#  penalty
# text = "Raheem Sterling penalty miss against Brighton"

# VAR
# text = "Tottenham Manchester United VAR Check for Penalty"

# UCL e UEL
# text = "Source at UEFA leagues who void seasons could find it difficult to nominate UCL and UEL reps ESPECIALLY if other leagues complete their comps Non completion could lead to non qualification could be seen that teams did not qualify if voided brings coefficient issues also"

# striker e forward e winger
# text = "Mythbuster Was Chelsea legend Drogba truly a world class striker"
# text = "Raúl Jiménez is the forward that Zidane wants for Real Madrid"
# text = "Managing Madrid Real Madrid ’s Winger Dilemma Broken Down by Data An in depth look at the numbers behind each of Real Madrid ’s wingers both at home and on loan"

# crossbar free kick
# text = "C.Ronaldo hits the crossbar from a free kick Spal Juventus"

# referee
# text = "Penalty shout from Barcelona against Betis not given by the referee"

# yellow card e red card
# text = "Nabil Fékir Bétis Second Yellow against Barcelona"
# text = "Tottenham Hotspur Vs Manchester City Raheem Sterling potential Red Card not given due to VAR"

# goal
# text = "Neymar has won the UCL player of the week and goal of the week for Matchday"

# PL
# text = "Premier League Jose Mourinho is the Manager of the Month for November"

# VAR
# text = "Video Assistant Referee Reverses Wolves PK Vs Liverpool"

# EPL
# text = "Tottenham Hotspur Manchester City EPL"

# shooting guard, center, forward,
# flagrant, ring, basket, block, guard, rebound, steal, conference


# words = ['ball', 'crossbar', 'free kick', 'referee', 'yellow card', 'red card', 'goal', 'striker', 'forward', 'winger', 'penalty', 'offside', 'goalkeeper', 'midfielder', 'defender']
# if any(word in text.lower() for word in words):
#     text, annotations = annotate_dandelion(text, confidence, sport)
# else:
#     text, annotations = annotate_dbpedia(text, confidence, sport)

#text = preprocessing("Dean Smith Lampard Time luxury given football year get play offs Derby Chelsea get FA Cup final UCL qualification transfer ban day ago league Technical director ex teammate")
#print(text)
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
    text = re.sub(r'_', ' ', text)
    # Rimuovo lo slash
    text = re.sub(r'/', ' ', text)
    # Rimuovo |
    text = re.sub(r'\|', ' ', text)
    # Rimuovo le parentesi dal testo
    text = re.sub(r'(\()([^)]+)(\))', '\g<2>', text)
    # Sostituisco ']' con '] '
    text = text.replace(']', '] ')
    # Rimuovo i numeri dal testo
    text = re.sub(r'(?<![a-zA-Z]-)(\b\d+\b)', ' ', text)
    # Rimuovo minuti / millioni
    text = re.sub(r'\d+m\b', ' ', text)
    # Rimuovo posizioni
    text = re.sub(r'\d+th\b', ' ', text)
    text = re.sub(r'\d+st\b', ' ', text)
    text = re.sub(r'\d+nd\b', ' ', text)
    text = re.sub(r'\d+rd\b', ' ', text)
    # Rimuovo ore
    text = re.sub(r'\d+h\b', ' ', text)
    text = re.sub(r'\d+am\b', ' ', text)
    text = re.sub(r'\d+pm\b', ' ', text)
    text = re.sub(r'(\b\d+h\d+\b)', ' ', text)
    # Rimouvo anni
    text = re.sub(r'\d+s\b', ' ', text)
    # Sostituisco statistiche
    text = re.sub(r'(\d+)(ppg)', ' ppg', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(pt(s?))', ' pts', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(reb(s?))', ' rebs', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(ast(s?))', ' asts', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(stl(s?))', ' stls', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(blk(s?))', ' blks', text, flags=re.IGNORECASE)
    # Sostituisco acronimo EPL
    text = re.sub(r'(\bEPL\b)', 'English Premier League', text)
    # Sostituisco acronimo PL
    text = re.sub(r'(\bPL\b)', 'Premier League', text)
    # Sostituisco acronimo VAR
    text = re.sub(r'(\bVAR\b)', 'Video Assistant Referee', text)
    # Sostituisco acronimo UCL
    text = re.sub(r'(\bUCL\b)', 'Uefa Champions League', text)
    # Sostituisco acronimo CL
    text = re.sub(r'(\bCL\b)', 'Champions League', text)
    # Sostituisco acronimo UEL
    text = re.sub(r'(\bUEL\b)', 'Uefa Europa League', text)
    # Sostituisco acronimo EL
    text = re.sub(r'(\bEL\b)', 'Europa League', text)
    # Sostituisco acronimo PPG
    text = re.sub(r'(\bppg\b)', 'points per game', text, flags=re.IGNORECASE)
    # Sostituisco acronimo PTS
    text = re.sub(r'(\bpt(s?)\b)', 'point', text, flags=re.IGNORECASE)
    # Sostituisco acronimo REBS
    text = re.sub(r'(\breb(s?)\b)', 'rebound', text, flags=re.IGNORECASE)
    # Sostituisco acronimo ASTS
    text = re.sub(r'(\bast(s?)\b)', 'assist', text, flags=re.IGNORECASE)
    text = re.sub(r'(\bassts\b)', 'assist', text, flags=re.IGNORECASE)
    # Sostituisco acronimo STL
    text = re.sub(r'(\bstl(s?)\b)', 'steal', text, flags=re.IGNORECASE)
    # Sostituisco acronimo BLK
    text = re.sub(r'(\bblk(s?)\b)', 'block', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FG
    text = re.sub(r'(\bFG\b)', 'field goal', text)
    # Sostituisco acronimo FT
    text = re.sub(r'(\bFT\b)', 'free throw', text, flags=re.IGNORECASE)
    # Rimuovo highlight(s)
    text = re.sub(r'(\bhighlight(s?)\b)', '', text, flags=re.IGNORECASE)
    # Rimuovo (pre/post)(-)(match thread)
    text = re.sub(r'(\bpost\b( ?))?(\bpre\b( ?))?(-?)(\bmatch\b) (\bthread\b)', '', text, flags=re.IGNORECASE)
    # Rimuovo (pre/post)(-)(game thread)
    text = re.sub(r'(\bpost\b( ?))?(\bpre\b( ?))?(-?)(\bgame\b) (\bthread\b)', '', text, flags=re.IGNORECASE)
    # Rimuovo (daily)(discussion)(thread)
    text = re.sub(r'(\bdaily\b( ?))?(\bdiscussion(s)?\b)(( ?)\bthread\b)?', '', text, flags=re.IGNORECASE)
    # Rimuovo breaking
    text = re.sub(r'(\bbreaking\b)', '', text, flags=re.IGNORECASE)
    # Rimuovo free talk friday
    text = re.sub(r'(\bfree talk friday\b)', '', text, flags=re.IGNORECASE)
    # Rimuovo VIDEO
    text = re.sub(r'(\bVIDEO\b)', '', text)
    # Rimuovo +
    text = re.sub(r'(\+)', '', text)
    # Rimuovo le valute
    text = text.replace('£', '')
    text = text.replace('$', '')
    text = text.replace('€', '')
    # Rimuovo i doppi spazi
    text = re.sub(r' {2,}', ' ', text)
    lemmas = [wnl.lemmatize(str(token)) for token in nlp(text) if not token.is_stop and not token.is_punct]
    text = " ".join(str(token) for token in lemmas if token != 'v')
    text = text.replace('Serie', 'Serie A')
    return text

text = "Tottenham 0 - [1] Liverpool - Roberto Firmino 45+4'"
print(preprocessing(text))



#s = sparql.Service('http://dbpedia.org/sparql', qs_encoding='utf-8')
#text, annotations = annotate(text, 'basketball', 'dandelion', 0.7)
#print('\n'+text)




import re
import time
from datetime import datetime
import emoji
import spacy
from nltk import WordNetLemmatizer
from psaw import PushshiftAPI
import praw
import datetime

from spacy.lang.char_classes import LIST_ELLIPSES, ALPHA_LOWER, LIST_ICONS, ALPHA_UPPER, CONCAT_QUOTES, ALPHA, HYPHENS
from spacy.util import compile_infix_regex
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
    text = re.sub(r'(\b\d+h\d+\b)', ' ', text)
    # Rimouvo anni
    text = re.sub(r'\d+s\b', ' ', text)
    # Sostituisco statistiche
    text = re.sub(r'(\d+)(ppg)', ' point per game', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(pt(s?))', ' point', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(reb(s?))', ' rebound', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(rpg)', ' rebound per game', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(ast(s?))', ' assist', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(apg)', ' assist per game', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(stl(s?))', ' steal', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(spg)', ' steal per game', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(blk(s?))', ' block', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(bpg)', ' block per game', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(OT(s?))', ' overtime', text)
    text = re.sub(r'(\d+)(pm)', ' three-point field goal made', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(pa)', ' three-point field goal attempted', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(P%)', ' three-point field goal', text)
    # Sostituisco acronimo ref
    text = re.sub(r'(\bTS%\b)', 'throw shooting percentage', text)
    # Sostituisco free-kick
    text = re.sub(r'(\bfree kick(s?)\b)', 'free-kick', text, flags=re.IGNORECASE)
    # Sostituisco free-throw'
    text = re.sub(r'(\bfree throw(s?)\b)', 'free-throw', text, flags=re.IGNORECASE)
    text = re.sub(r'(\bfreethrown(s?)\b)', 'free-throw', text, flags=re.IGNORECASE)
    # Sostituisco acronimo ref
    text = re.sub(r'(\bthrow%\b)', 'throw shooting percentage', text)
    # Sostituisco acronimo ref
    text = re.sub(r'(\bfield goal%\b)', 'field goal', text)
    # Sostituisco acronimo ref
    text = re.sub(r'(\bref\b)', 'referee', text, flags=re.IGNORECASE)
    # Sostituisco acronimo ref
    text = re.sub(r'(\bOT\b)', 'overtime', text)
    # Sostituisco acronimo ET
    text = re.sub(r'(\bET\b)', 'extra-time', text)
    # Sostituisco acronimo WC
    text = re.sub(r'(\bWC\b)', 'World Cup', text)
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
    # Sostituisco acronimo SG
    text = re.sub(r'(\bsg\b)', 'shooting guard', text, flags=re.IGNORECASE)
    # Sostituisco acronimo G
    text = re.sub(r'(\bg\b)', 'shooting guard', text, flags=re.IGNORECASE)
    # Sostituisco acronimo C
    text = re.sub(r'(\bc\b)', 'center', text, flags=re.IGNORECASE)
    # Sostituisco acronimo PF
    text = re.sub(r'(\bpf\b)', 'power forward', text, flags=re.IGNORECASE)
    # Sostituisco acronimo SF
    text = re.sub(r'(\bsf\b)', 'small forward', text, flags=re.IGNORECASE)
    # Sostituisco acronimo F
    text = re.sub(r'(\bf\b)', 'forward', text, flags=re.IGNORECASE)
    # Sostituisco acronimo PPG
    text = re.sub(r'(\bppg\b)', 'point per game', text, flags=re.IGNORECASE)
    # Sostituisco acronimo PTS
    text = re.sub(r'(\bpt(s?)\b)', 'point', text, flags=re.IGNORECASE)
    # Sostituisco acronimo REBS
    text = re.sub(r'(\breb(s?)\b)', 'rebound', text, flags=re.IGNORECASE)
    # Sostituisco acronimo RPG
    text = re.sub(r'(\brpg\b)', 'rebound per game', text, flags=re.IGNORECASE)
    # Sostituisco acronimo ASTS
    text = re.sub(r'(\bast(s?)\b)', 'assist', text, flags=re.IGNORECASE)
    text = re.sub(r'(\bassts\b)', 'assist', text, flags=re.IGNORECASE)
    # Sostituisco acronimo APG
    text = re.sub(r'(\bapg\b)', 'assist per game', text, flags=re.IGNORECASE)
    # Sostituisco acronimo STL
    text = re.sub(r'(\bstl(s?)\b)', 'steal', text, flags=re.IGNORECASE)
    # Sostituisco acronimo SPG
    text = re.sub(r'(\bspg(s?)\b)', 'steal per game', text, flags=re.IGNORECASE)
    # Sostituisco acronimo BLK
    text = re.sub(r'(\bblk(s?)\b)', 'block', text, flags=re.IGNORECASE)
    # Sostituisco acronimo BPG
    text = re.sub(r'(\bblk(s?)\b)', 'block per game', text, flags=re.IGNORECASE)
    # Sostituisco triple-double
    text = re.sub(r'(\btriple double\b)', 'triple-double', text, flags=re.IGNORECASE)
    # Sostituisco double-double
    text = re.sub(r'(\bdouble double\b)', 'double-double', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FGM
    text = re.sub(r'(\bFGM\b)', 'field goal made', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FGA
    text = re.sub(r'(\bFGA\b)', 'field goal attempted', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FG
    text = re.sub(r'(\bFG\b)', 'field goal', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FTM
    text = re.sub(r'(\bFTM\b)', 'free throw made', text, flags=re.IGNORECASE)
    # Sostituisco acronimo FTA
    text = re.sub(r'(\bFTA\b)', 'free throw attempted', text, flags=re.IGNORECASE)
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
    # rimuovo acronimo OC
    text = re.sub(r'(\bOC\b)', '', text)
    # Rimuovo i doppi spazi
    text = re.sub(r' {2,}', ' ', text)
    lemmas = [token for token in nlp(text) if not token.is_stop and not token.is_punct]
    text = " ".join(str(token) for token in lemmas)
    text = text.replace('Serie', 'Serie A')
    return text


def start_scraping(subreddit, months, filename, limit, from_date):
    after = from_date
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
                if limit:
                    for count, submission in enumerate(api.search_submissions(subreddit=subreddit,
                                                                              before=temp,
                                                                              sort_type="num_comments",
                                                                              sort="desc",
                                                                              limit=limit,
                                                                              after=after_week,
                                                                              fields=["id", "title", "created_utc"])):
                        # Rimuovo i simboli non necessari
                        text = preprocessing(submission.title)
                        date = str(datetime.datetime.fromtimestamp(submission.created_utc))[0:10]
                        if len(text) > 2:
                            print("\t\t{} - {} - {}".format(count, date, submission.title))
                            print("\t\t{} - {} - {}\n".format(count, date, text))
                            f.write(text + "\n")
                else:
                    for count, submission in enumerate(api.search_submissions(subreddit=subreddit,
                                                                              before=temp,
                                                                              sort_type="num_comments",
                                                                              sort="desc",
                                                                              after=after_week,
                                                                              fields=["id", "title", "created_utc"])):
                        # Rimuovo i simboli non necessari
                        text = preprocessing(submission.title)
                        date = str(datetime.datetime.fromtimestamp(submission.created_utc))[0:10]
                        if len(text) > 2:
                            print("\t\t{} - {} - {}".format(count, date, submission.title))
                            print("\t\t{} - {} - {}\n".format(count, date, text))
                            f.write(text + "\n")
                total = total + count
                print("\ttotal submissions: {}".format(total))
                time.sleep(10)


if __name__ == '__main__':
    subreddit = input(f'subreddit: ')
    from_date = input(f'from (dd/mm/yyyy): ')
    months = input(f'months: ')
    filename = input(f'output filename: ')
    limit = input(f'limit: ')
    reddit = praw.Reddit(
        client_id="",
        client_secret="",
        user_agent=""
    )
    wnl = WordNetLemmatizer()
    api = PushshiftAPI(reddit)
    nlp = spacy.load("en_core_web_sm")
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
    from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y')
    if limit:
        start_scraping(str(subreddit), int(months), str(filename), int(limit), from_date)
    else:
        start_scraping(str(subreddit), int(months), str(filename), None, from_date)

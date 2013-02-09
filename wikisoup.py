from bs4 import SoupStrainer, BeautifulSoup
from collections import defaultdict
import urllib2, urlparse
import ujson as json
import pprint as pp
import redis
import random
import re

STOP_WORDS = list(set(["a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both",
    "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
    "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither",
    "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
    "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
    "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
    "please", "put", "rather", "re", "same", "see", "seem", "seemed",
    "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
    "something", "sometime", "sometimes", "somewhere", "still", "such",
    "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they", "thick", "thin",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet", "you", "your", "yours", "yourself","yourselves"]))

WORDS = re.compile('(?u)\\b[A-Za-z]{3,}', re.IGNORECASE|re.DOTALL)

def count_words(text, ngram_range=(1,1), 
                tokens=WORDS, stop_words=STOP_WORDS):
    
    words = [word.lower() for word in tokens.findall(text)
            if word.lower() not in stop_words]

    ngram_counts = defaultdict(int)

    for i in range(len(words)):
        for n in range(1, ngram_range[1] + 1):
            if i + n <= len(words):
                ngram = ' '.join(words[i:i + n])
                ngram_counts[(n, ngram)] += 1

    return dict(ngram_counts)

def read_page(url, verbose=False):
    header = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url, headers=header)

    if verbose:
        print "opening: %s" % url
    
    try:
        page = urllib2.urlopen(req).read()
    except e:
        print 'ERROR'
        print e.fn.read()
        page = ''
    
    return page

def find_all_urls(url, html, verbose=False, publish=False):
    corpus = get_corpus(html)
    vocab  = count_words(corpus)
    if verbose:
        pp.pprint(vocab)
    
    if publish:
        r.publish('wordcounts', json.dumps(vocab))

    css = {"class": "featured_article_metadata"}
    for span in BeautifulSoup(html).find_all('span', css):
        a = span.find('a')    
        if a and "href" in a.attrs:
            next_page = 'http://en.wikipedia.org' + a['href']
            seen.add(url)
            if next_page in seen: return

            find_all_urls(next_page, read_page(next_page, verbose), verbose)

def get_corpus(html):
    css = "mw-content-text"
    content = BeautifulSoup(html).find(id=css)
    text = ""
    if content:
        for p in content.find_all('p'):
            text += p.get_text() + "\n\n"
    return text

r = redis.StrictRedis()
domains = {}
seen = set()
seed = 'http://en.wikipedia.org/wiki/Wikipedia:Featured_articles'

find_all_urls(seed, read_page(seed, verbose=True), verbose=True)



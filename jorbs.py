import asyncio
from bs4 import BeautifulSoup
import feedparser #pip3 install feedparser
import hashlib
import html 
import os
from pyppeteer import launch
from pyppeteer_stealth import stealth
import re
import time
import tldextract
import urllib


from jorbs_config import *
from jorbs_functions import *


time_stamp = int(time.time()) #have a conistent timestamp for all of the logging from the start of the run

aggregators_rss_url = []
for aggregator in aggregators_rss:
    print(f"rss: {aggregator}")
    for keyword in search_keywords:
        print(f"\tkeyword: {keyword}")

        keyword_encded = urllib.parse.quote_plus(keyword) #urlencode the search string -- ie spaces turn to %20.
        url = f"{aggregator}{keyword_encded}" #build the actual url for collection 

        feed_raw = get_feed(url)

        links = get_links_from_feed(feed_raw) #get the links from the feed

        write_feed_log(aggregator,keyword,time_stamp,feed_raw)

        for link in links:
            print(f"\t\tlink: {link}")


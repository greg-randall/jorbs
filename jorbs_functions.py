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

# download the feed using pyppeteer (some of the sites will return junk if you just do a standard download)
def get_feed(url): 
    async def get_feed_raw(): #startin up the pyppeteer
        browser = await launch()
        page = await browser.newPage()

        await stealth(page) #lookin at you indeed

        await page.goto(url)
        feed_raw = await page.content()
        await browser.close()

        return feed_raw

    feed_raw = asyncio.get_event_loop().run_until_complete(get_feed_raw()) #get the feed output

    feed_raw = html.unescape(feed_raw) #unescape the feed, sometimes feeds come from pyppeteer with the xml brackets encoded

    return feed_raw


# then collect the links from the rss feed
def get_links_from_feed(feed_raw): 
    raw_links = re.findall('<link>h[^<]*</link>', feed_raw) #using regex for the feed link collection. feeds are that come out of pyppeteer are malformed since chrome formats them

    output_links = []

    if len(raw_links)>1:

        for link in raw_links:
            link = re.sub('</?link>','', link) #remove the link tag from around the link
            link = html.unescape(link) #xml requires that ampersands be escaped, fixing that for our links
            
            output_links.append(link) #add the clean link to our output 

        output_links.pop(0) #first link in an rss feed is a link to the site associated with the feed https://www.rssboard.org/rss-draft-1#element-channel-link

        if output_links[0] == "https://www.indeed.com/": #indeed sometimes outputs an extra link to itself at the start of the file
           output_links.pop(0) 

    return output_links


#write out the feed
def write_feed_log(aggregator,keyword,time_stamp,feed_raw): 
    if not os.path.exists("jorbs_feeds"):#make feed log folder if it doesn't exist
        os.mkdir("jorbs_feeds") 

    if not os.path.exists(f"jorbs_feeds/{time_stamp}"):#make feed log subfolder folder if it doesn't exist
        os.mkdir(f"jorbs_feeds/{time_stamp}") 

    domain = tldextract.extract(aggregator) #get domain by itself for feed logging filenames
    domain = domain.domain

    keyword_clean = re.sub('"','', keyword) #clean the keywords for logging filenames
    keyword_clean = re.sub('[^a-zA-Z_-]','_', keyword_clean)

    f = open(f"jorbs_feeds/{time_stamp}/{domain}_{keyword_clean}_{int(time.time())}.xml", "w") #write out the raw feed for reference
    f.write(feed_raw)
    f.close()




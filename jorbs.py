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
    async def get_raw_feed(): #startin up the pyppeteer
        browser = await launch()
        page = await browser.newPage()

        await stealth(page) #lookin at you indeed

        await page.goto(url)
        raw_feed = await page.content()
        await browser.close()

        return raw_feed

    raw_feed = asyncio.get_event_loop().run_until_complete(get_raw_feed()) #get the feed output

    raw_feed = html.unescape(raw_feed) #unescape the feed, sometimes feeds come from pyppeteer with the xml brackets encoded

    return raw_feed

# then collect the links from the rss feed
def get_links_from_feed(raw_feed): 
    raw_links = re.findall('<link>h[^<]*</link>', raw_feed) #using regex for the feed link collection. feeds are frequently malfored in ways that make the standard feedparser library throw errors

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







#aggregators, format so that the keyword part is at the end
aggregators_rss = ["https://careers.insidehighered.com/jobsrss/?countrycode=US&keywords=","https://www.timeshighereducation.com/unijobs/jobsrss/?keywords=","https://main.hercjobs.org/jobs/?display=rss&keywords=","https://jobs.chronicle.com/jobsrss/?countrycode=US&keywords=","http://rss.indeed.com/rss?q=","https://www.acad.jobs/rss/rss.php?cnt=us&cat=268,253,254,263,256,272,273,290,292,293,294,274,275&st=1&ju=1&se=1&a=1&p=1&q="]

#search keywords, add in double quotes as needed
search_keywords = ['"book arts"','letterpress','"artist books"','"book binding"','"handmade paper"','"book conservation"','papermaking','bookbinder','"book conservator"','"fine press"']

#make feed log folder:
if not os.path.exists("jorbs_feeds"):
    os.mkdir("jorbs_feeds") 

aggregators_rss_url = []
for aggregator in aggregators_rss:
    print(f"rss: {aggregator}")

    domain = tldextract.extract(aggregator) #get domain by itself for feed logging filenames
    domain = domain.domain

    for keyword in search_keywords:
        print(f"\tkeyword: {keyword}")
        keyword_encded = urllib.parse.quote_plus(keyword) #urlencode the search string -- ie spaces turn to %20.
        url = f"{aggregator}{keyword_encded}" #build the actual url for collection 

        feed_raw = get_feed(url)

        keyword_clean = re.sub('"','', keyword) #clean the keywords for logging filenames
        keyword_clean = re.sub('[^a-zA-Z_-]','_', keyword_clean)

        f = open(f"jorbs_feeds/{domain}_{keyword_clean}_{int(time.time())}.xml", "w") #write out the raw feed for reference
        f.write(feed_raw)
        f.close()

        links = get_links_from_feed(feed_raw) #get the links from the feed
        for link in links:
            print(f"\t\tlink: {link}")


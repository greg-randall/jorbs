import asyncio
from bs4 import BeautifulSoup
from csv import writer
import datetime
import html
import openai
import os
from pyppeteer import launch
from pyppeteer_stealth import stealth
import re
import time
import tldextract
import uuid



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

    try:
        feed_raw = asyncio.get_event_loop().run_until_complete(get_feed_raw()) #get the feed output
    except:
        return False

    feed_raw = html.unescape(feed_raw) #unescape the feed, sometimes feeds come from pyppeteer with the xml brackets encoded

    return feed_raw


# then collect the links from the rss feed
def get_links_from_feed(feed_raw): 
    raw_links = re.findall('<link>h[^<]*</link>', feed_raw) #using regex for the feed link collection. feeds are that come out of pyppeteer are malformed since chrome formats them

    output_links = []
    output_links_clean = []

    if len(raw_links)>1:

        for link in raw_links:
            link = re.sub('</?link>','', link) #remove the link tag from around the link
            link = html.unescape(link) #xml requires that ampersands be escaped, fixing that for our links
            
            output_links.append(link) #add the clean link to our output 

        output_links.pop(0) #first link in an rss feed is a link to the site associated with the feed https://www.rssboard.org/rss-draft-1#element-channel-link

        if output_links[0] == "https://www.indeed.com/": #indeed sometimes outputs an extra link to itself at the start of the file
           output_links.pop(0) 

        #going to clean the links a bit, most links have some query string stuff that isn't needed, exceept indeed, which has the job id in the query string.
        #doing this so that we lose all the unique tracking IDs or whatever on the link, so later on it'll be easier to see if we've already looked at a link.
        for output_link in output_links:
            domain = tldextract.extract(output_link) #get domain by itself
            domain = domain.domain
            if domain =="indeed":
                output_links_clean.append(output_link.split("&rtk=", 1)[0]) #indeed keeps a job id in the query string, but the text after 'rtk' isn't needed and changes
            else:
                output_links_clean.append(output_link.split("?", 1)[0])


    return output_links_clean


#write out the feed
def write_log_item(path,aggregator,keyword,timestamp,feed_raw): 
    if not os.path.exists(path):#make feed log folder if it doesn't exist
        os.mkdir(path) 

    if not os.path.exists(f"{path}"):#make feed log subfolder folder if it doesn't exist
        os.mkdir(f"{path}") 

    domain = tldextract.extract(aggregator) #get domain by itself for feed logging filenames
    domain = domain.domain


    keyword_clean = re.sub('"','', keyword) #clean the keywords for logging filenames
    keyword_clean = re.sub('[^a-zA-Z_-]','_', keyword_clean)


    f = open(f"{path}/{domain}_k-{keyword_clean}_t-{int(time.time())}_uuid-{uuid.uuid4().hex}.txt", "w") #write out the raw feed for reference
    f.write(feed_raw)
    f.close()

#download the feed using pyppeteer (some of the sites will return junk if you just do a standard download)
def get_jorb(url):
    #wrapper class for part of the page we're interested in.
    #find the smallest class that wraps the entire job description
    jobsite_container_class={ 
        "indeed": "jobsearch-JobComponent",
        "chronicle": "mds-surface",
        "insidehighered": "mds-surface",
        "hercjobs": "bti-job-detail-pane",
        "timeshighereducation": "js-job-detail",
    }

    domain = tldextract.extract(url)
    domain = domain.domain

    
    async def get_page(): #startin up the pyppeteer
        browser = await launch()
        page = await browser.newPage()

        await stealth(page) #lookin at you indeed

        await page.goto(url)

        page = await page.content()
        await browser.close()

        return page

    try:
        page = asyncio.get_event_loop().run_until_complete(get_page()) #get the page raw output
    except:
        return False

    soup = BeautifulSoup(page,features="lxml") #start up beautifulsoup

    #remove script and style tags, sometimes since we're getting the text out of all the tags, these get mixed in and give a lot of bad data
    for script_tags in soup.select('script'): 
        script_tags.extract()
    for style_tags in soup.select('style'): 
        style_tags.extract()


    #need to do some per-site cleaning to remove extra text:
    if domain == "hercjobs":
        for div in soup.find_all("div", {'class':'d-print-none'}): 
            div.decompose()
        for button_tags in soup.select('button'): 
            button_tags.extract()
        for div in soup.find_all("div", {'modal'}): 
            div.decompose()

    if domain == "insidehighered" or domain == "chronicle":
        for div in soup.find_all("div", {'mds-text-align-right'}):
            div.decompose()
        for div in soup.find_all("div", {'mds-border-top'}):
            div.decompose()

    if domain == "timeshighereducation":
        for ul in soup.find_all("ul", {'job-actions'}):
            ul.decompose()
        for div in soup.find_all("div", {'float-right'}):
            div.decompose()
        for div in soup.find_all("div", {'premium-disabled'}):
            div.decompose()
        for span in soup.find_all("span", {'hidden'}):
            span.decompose()
        for div in soup.find_all("div", {'job-sticky-ctas'}):
            div.decompose()

    if domain in jobsite_container_class.keys():
        elements = soup.find_all("div", class_ = jobsite_container_class[domain]) #need to find
        try:
            text = elements[0].get_text(separator=' ') #get text but add spaces around elements
        except IndexError:
            text = soup.get_text(separator=' ')
        
    else:
        print(f"NOTE: did not recognize jobsite {domain}, consider adding to get_jorb function")
        text = soup.get_text(separator=' ')

    
    text = html.unescape(text) #fixes html escaped text, like the &nbsp; nonbreaking space
    text = re.sub('[^\S\r\n]+', ' ', text) #remove doubled spaces
    text = re.sub('\n+\s*\n+','\n', text) #remove extra linebreaks
    text = re.sub('\n\s+','\n', text) #remove spaces at the start of lines
    
    return text


#get chatgpt to parse our job
def gpt_jorb_parse(gpt_base_prompt,job_description,open_ai_key):
    openai.api_key = open_ai_key

    prompt = f"{gpt_base_prompt}{job_description}" #build our prompt
    
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    except:
        return False
    
    reply = completion.choices[0].message.content #just get the reply message which is what we care about
    return reply

def split_gpt(read_job,job_link):
    read_job = read_job.splitlines() #split the chat output by linebreaks

    read_job.reverse() #this is probably showing my python inexpereince, but fipping to prepend data
    read_job.append(job_link)

    d_date = datetime.datetime.now()
    read_job.append(d_date.strftime("%m-%d-%Y %I:%M%p"))

    read_job.reverse()

    read_job = [s.strip() for s in read_job] #strip lealding/trailing whitespace

    return read_job


def write_jorb_csv_log(output,timestamp):
    with open(f"jorb_run_{timestamp}/collected_jorbs_{timestamp}.csv", 'a') as f_object: #write the output as a csv
        writer_object = writer(f_object)
        writer_object.writerow(output)
        f_object.close()
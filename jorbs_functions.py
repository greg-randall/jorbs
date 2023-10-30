import asyncio
from bs4 import BeautifulSoup
from collections import OrderedDict
from csv import writer
import html
import openai
import os
from pyppeteer import launch
from pyppeteer_stealth import stealth
import re
import requests
import time
import tldextract
import uuid
import json


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


#collect the links from the rss feed
def get_links_from_feed(feed_raw): 
    raw_links = re.findall('<link>h[^<]*</link>', feed_raw) #using regex for the feed link collection. feeds are that come out of pyppeteer are malformed since chrome formats them

    output_links = []
    output_links_clean = []

    if len(raw_links)>1: #make sure we actually got some links

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
                output_links_clean.append(output_link.split("&rtk=", 1)[0]) #indeed keeps the job id in the query string, but the text after 'rtk' changes (and isn't needed), which would break our system of ignoring previously processed links
            else:
                output_links_clean.append(output_link.split("?", 1)[0]) #toss everything after the question mark

    return output_links_clean


#write out the feed
def write_log_item(path,aggregator,keyword,timestamp,feed_raw): 
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
    #wrapper html class for part of the page we're interested in.
    #find the smallest div with a class that wraps the entire job description
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

    #remove script and style tags, sometimes since we're getting the text out of all the tags, these get mixed in sometimes and give a lot of bad data
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

    if domain in jobsite_container_class.keys(): #see if we see the current domain in our list of domains that we have classes for
        elements = soup.find_all("div", class_ = jobsite_container_class[domain]) #find the container
        try:
            text = elements[0].get_text(separator=' ') #get text but add spaces around elements
        except IndexError:
            text = soup.get_text(separator=' ') #if we don't find the container, we'll just get all the text, and throw an error
            print(f"NOTE: {domain}'s container div wasn't found. might want to read the get_jorb function")
        
    else:
        print(f"NOTE: did not recognize jobsite {domain}, consider adding to get_jorb function")
        text = soup.get_text(separator=' ') #we'll just get all the text, and throw an error

    
    text = html.unescape(text) #fixes html escaped text, like the &nbsp; nonbreaking space
    text = re.sub('[^\S\r\n]+', ' ', text) #remove doubled spaces
    text = re.sub('\n+\s*\n+','\n', text) #remove extra linebreaks
    text = re.sub('\n\s+','\n', text) #remove spaces at the start of lines
    
    return text


def write_jorb_csv_log(output,timestamp): #this is our output file 
    filename = f"jorb_run_{timestamp}/collected_jorbs_{timestamp}.csv"
    if not os.path.exists(filename):#if the output file doesn't exist yet we'll add a header
        header = list(output.keys())

        #this header is coming directly from the output ,we'll clean the output a bit
        header.sort() 
        header.remove('1_date_time')
        header.remove('2_job_link')
        header = ['job_link'] + header
        header = ['date_time'] + header
    
        
        with open(filename, 'a') as f_object: #write the csv header
            writer_object = writer(f_object)
            writer_object.writerow(header)
            f_object.close()

    #write the output line to the csv
    with open(filename, 'a') as f_object: #write the output as a csv
        writer_object = writer(f_object)
        writer_object.writerow(output.values())
        f_object.close()


#reference https://blog.daniemon.com/2023/06/15/chatgpt-function-calling/
def gpt_jorb(jorb,open_ai_key,functions,field_name,relevance):

    #do the chat gpt function request
    try:
        openai.api_key = open_ai_key
        response = openai.ChatCompletion.create(
            #model = "gpt-3.5-turbo-0613",
            model = "gpt-4-0613",
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at reading job descriptions, and determing the kind of job, job requirements, job salary, job location, and other job information."
                },
                {
                    "role": "user",
                    "content": jorb
                }
            ],
            functions = functions,
            function_call = {
                "name": functions[0]["name"]
            }
        )

        #gets the structured response
        arguments = response["choices"][0]["message"]["function_call"]["arguments"]


        arguments = re.sub("\n", ' ', arguments) #remove linebreaks inside the json fields,
        arguments = re.sub("\s+", ' ', arguments) #remove doubled spaces in the json
        
        #parses the structured response
        arguments = json.loads(arguments)
        
        for key in functions[0]['parameters']['required']: #make sure that if chatgpt fails to return a value we add it in so the output csv isn't a mess
            if not key in arguments:
                arguments[key] = "null"

        #we're going to do a followup question for chatgpt to try and figure out if the job is actually relevant to our interests
        try:
            prompt = f"{relevance}\n\nJob Description:\n{arguments['summary']}\n\nJob Requirements:\n{arguments['requirements']}" #build our prompt

            openai.api_key = open_ai_key
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
            reply = completion.choices[0].message.content #just get the reply message which is what we care about

            reply = re.sub("\n", ' ', reply) #remove linebreaks
            reply = re.sub("\s+", ' ', reply) #remove doubled spaces

            arguments[field_name]=reply

        except:
            return False

        arguments = OrderedDict(sorted(arguments.items()))#sort our output
        return arguments
    
    except:
        return False

#text message function
def send_text(phone,message,api_key):
    resp = requests.post('https://textbelt.com/text', {
    'phone': phone,
    'message': message,
    'key': api_key,
    })
    #print(resp.json())
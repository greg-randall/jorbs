import time
import urllib
import random
import os

from jorbs_config import * #make sure to copy and rename 'jorbs_config_blank.py' to  'jorbs_config.py'
from jorbs_functions import *

#randomize list order, so if we are getting rate limited or something on one of the sites, the keywords happen in different orders
random.shuffle(aggregators_rss)
random.shuffle(search_keywords)

timestamp = int(time.time()) #have a conistent timestamp for all of the logging from the start of the run

if not os.path.exists(f"jorb_run_{timestamp}"):#make feed log subfolder folder if it doesn't exist
    os.mkdir(f"jorb_run_{timestamp}") 


#read in the list of previous checked urls, so we don't process them again:
if os.path.exists("already_parsed_jobs.txt"):
    my_file = open("already_parsed_jobs.txt", "r") 
    data = my_file.read() 
    already_processed_jobs = data.split("\n") 
    my_file.close()
else:
    already_processed_jobs = [] #if the file doesn't exist, we'll just make a blank file


job_links_skip = [] #we're going to skip links that have already been processed, during this run


for aggregator in aggregators_rss:
    print(f"feed: {aggregator}")
    for keyword in search_keywords:
        print(f"  keyword: {keyword}")

        keyword_encded = urllib.parse.quote_plus(keyword) #urlencode the search string -- ie spaces turn to %20, quotes to %22.
        
        url = f"{aggregator}{keyword_encded}" #build the url for collection 

        feed_raw = get_feed(url)

        if feed_raw:
            
            write_log_item(f"jorb_run_{timestamp}/feeds",aggregator,keyword,timestamp,feed_raw) #logging the feeds for later troubleshooting

            job_links = get_links_from_feed(feed_raw) #get the links from the feed

            for job_link in job_links:

                print(f"    job: {job_link}")


                if job_link in already_processed_jobs or job_link in job_links_skip: #check to see if the job link we're looking at has been processed in this or a previous run
                    print(f"      job processed previously")
                else:
                    job_description = get_jorb( job_link ) #collect the page with the job description
                    if job_description:

                        write_log_item(f"jorb_run_{timestamp}/job_listings",job_link,keyword,timestamp,job_description)  #logging the description for later troubleshooting

                        read_job = gpt_jorb(job_description,open_ai_key,functions,relevance_field_name,relevance)

                        if read_job:

                            print(f"      data: {read_job}")

                            #add datetime and the link to our job info for output
                            read_job['1_date_time'] = time.strftime("%m-%d-%Y %I:%M%p")
                            read_job['2_job_link'] = job_link


                            read_job = OrderedDict(sorted(read_job.items()))#sort the output


                            write_jorb_csv_log(read_job,timestamp)

                            
                            file1 = open("already_parsed_jobs.txt", "a")  #output the url of the job we just parsed, so we don't do it again in future runs
                            file1.write(f"{job_link}\n")
                            file1.close()

                            job_links_skip.append(job_link) #append the url of the job we just parsed to an array, so if it comes up in this run again, we skip it

                            #determining if we're going to text ourselves about a new job
                            text_or_not = read_job[relevance_field_name].lower() #make the string lowercase for comparison

                            if text_or_not == "true": #if string is true send a text:
                                message = f"{read_job['1_date_time']}\nPossible New Job: {read_job['job-title']}\n{read_job['2_job_link']}"

                                if not send_text(phone_number,message,textbelt_key):
                                    print ("ERROR: something went wrong when we tried to send a text, check your textbelt API key and your phone number")

                        else:
                            print ("ERROR: something happened with the above job when we asked chatgpt to parse the info")
                    else:
                        print ("ERROR: something happened with the above job in when we tried to get the job description")                    
        else:
            print ("ERROR: something happened with the above rss feed when we tried to download it")
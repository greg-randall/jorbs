import os
import random
from termcolor import cprint
import textwrap
import time
import urllib

from jorbs_config import * #make sure to copy and rename 'jorbs_config_blank.py' to  'jorbs_config.py'
from jorbs_functions import *

#randomize list order, breaks the pattern up of us searching the websites 
random.shuffle(search_keywords)
random.shuffle(aggregators_rss)

timestamp = int(time.time()) #have a conistent timestamp for all of the logging from the start of the run

#read in the list of previous checked urls, so we don't process them again:
if os.path.exists("already_parsed_jobs.txt"):
    my_file = open("already_parsed_jobs.txt", "r") 
    data = my_file.read() 
    already_processed_jobs = data.split("\n") 
    my_file.close()
    #print(f"already processed jobs: {len(already_processed_jobs)}\n\n")
else:
    already_processed_jobs = [] #if the file doesn't exist, we'll just make a blank file


job_links_skip = [] #we're going to skip links that have already been processed, during this run

text_sent = False #we'll check to see if any texts were sent, if none were we'll send one letting us know that the scan ran

total_jobs_scanned = 0
total_jobs_skipped = 0
for keyword in search_keywords:
    cprint(f"keyword: {keyword}", "red")
    for aggregator in aggregators_rss:
        
        domain = get_domain(aggregator)

        if not domain == "linkedin": #linkedin is handled differently,
            #urlencode the search string -- ie spaces turn to %20, quotes to %22.
            url = f"{aggregator}{urllib.parse.quote_plus(keyword)}" #build the url for collection 
        elif domain == "linkedin":
            linked_in_keyword = keyword.replace('"', '')
            linked_in_keyword =urllib.parse.quote_plus(linked_in_keyword)
            url = f"{aggregator}{linked_in_keyword}" #build the url for collection
        
        cprint(f"  {url}", "yellow")

        if domain == "linkedin": #linkedin is handled differently,
            job_links = get_linkedin_search(url)
        elif domain == "careerjet":
            job_links = get_careerjet_job_links(keyword)
        else:
            feed_raw = get_feed(url)
            job_links = get_links_from_feed(feed_raw)
            

        no_jobs_found = 0
        job_counter = 1
        if isinstance(job_links, list): #make sure the item is a list
            skipped_jobs=0
            not_skipped_jobs=0
            keyword_not_found = 0
            for job_link in job_links:
                total_jobs_scanned += 1
                if not job_link in already_processed_jobs and not job_link in job_links_skip: #check to see if the job link we're looking at has been processed in this or a previous run
                    job_description = get_jorb( job_link ) #collect the page with the job description
                    if job_description:        

                        #we're going to make sure that at least one of our keywords is in the job description, if not we'll skip the job description
                        keyword_found = False
                        for search_keyword in search_keywords:
                            keyword_no_quotes = search_keyword.replace('"', '')
                            if keyword_no_quotes.lower() in job_description.lower():
                                keyword_found = True
                                break

                        if keyword_found:
                            cprint(f"      job: {job_link}","green")
                            cprint(f"        {search_keyword} found in job description, starting gpt","green") #if we do find the keyword, we'll fire up chatgpt
                            read_job = gpt_jorb(job_description,open_ai_key,functions,relevance_field_name,relevance)
                        else: #if we don't find the keyword, we'll skip the job, and write it out to our already processed jobs file and our skip list
                            print(f"      {job_counter}: {job_link}")
                            print(f"        none of the keywords were found in the job description")
                            read_job = False

                            file1 = open("already_parsed_jobs.txt", "a")  #output the url of the job so we don't do it again in future runs
                            file1.write(f"{job_link}\n")
                            file1.close()

                            job_links_skip.append(job_link) #append the url of the job, so if it comes up in this run again, we skip it
                            job_counter += 1

                        if read_job:
                            for key, value in read_job.items():
                                # Convert value to string
                                value = str(value)
                                wrapped_value = textwrap.fill(value, width=80, subsequent_indent='            ',initial_indent='            ')
                                cprint(f"          {key}:\n{wrapped_value}","green")
                            print("\n")
                            #add datetime and the link to our job info for output
                            read_job['1_date_time'] = time.strftime("%m-%d-%Y %I:%M%p")
                            read_job['2_job_link'] = job_link

                            read_job = OrderedDict(sorted(read_job.items()))#sort the output

                            write_jorb_csv_log(read_job,timestamp)

                            file1 = open("already_parsed_jobs.txt", "a")  #output the url of the job we just parsed, so we don't do it again in future runs
                            file1.write(f"{job_link}\n")
                            file1.close()

                            job_links_skip.append(job_link) #append the url of the job we just parsed to an array, so if it comes up in this run again, we skip it

                            if text_me_if(read_job):
                                message = f"{read_job['1_date_time']}\nTitle: {read_job['job-title'].title()}\nSummary: {read_job['summary'][:250]}...\n{read_job['2_job_link']}"
                                if not send_text(phone_number,message,textbelt_key):
                                    cprint ("ERROR: something went wrong when we tried to send a text, check your textbelt API key and your phone number", "magenta")

                        elif not keyword_found:
                            keyword_not_found += 1
                        else:
                            cprint ("ERROR: something happened with the above job when we asked chatgpt to parse the info", "magenta")
                    else:
                        cprint ("ERROR: something happened with the above job in when we tried to get the job description", "magenta")      
                else:
                    skipped_jobs+=1
                    total_jobs_skipped += 1
            if skipped_jobs > 0:
                print(f"      Skipped  {skipped_jobs} jobs that we had already seen.")
            else:
                not_skipped_jobs+=1
                #print(f"      No jobs skipped.")
        elif job_links == 0:
            #print ("      No jobs found")
            no_jobs_found += 1
        else:
           cprint ("ERROR: something happened with the above rss feed when we tried to download it", "magenta")
if not text_sent:
    message = f"{time.strftime('%m-%d-%Y %I:%M%p')}\nJob scan ran, but nothing to report"
    if not send_text(phone_number,message,textbelt_key):
        cprint ("ERROR: something went wrong when we tried to send a text, check your textbelt API key and your phone number", "magenta")


cprint(f"\n\nScanned {total_jobs_scanned} jobs\nFound {total_jobs_scanned-total_jobs_skipped} new jobs.\n","green")
import time
import urllib
import random
import os

from jorbs_config import * #make sure to copy and rename 'jorbs_config_blank.py' to  'jorbs_config.py'
from jorbs_functions import *

#randomize list order
random.shuffle(aggregators_rss)
random.shuffle(search_keywords)

timestamp = int(time.time()) #have a conistent timestamp for all of the logging from the start of the run

if not os.path.exists(f"jorb_run_{timestamp}"):#make feed log subfolder folder if it doesn't exist
    os.mkdir(f"jorb_run_{timestamp}") 

aggregators_rss_url = []
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

                job_description = get_jorb( job_link ) #collect the page with the job description
                if job_description:

                    write_log_item(f"jorb_run_{timestamp}/job_listings",job_link,keyword,timestamp,job_description)  #logging the description for later troubleshooting

                    read_job = gpt_jorb_parse(gpt_base_prompt,job_description,open_ai_key)

                    if read_job:
                        final_job_output = split_gpt(read_job,job_link)

                        write_jorb_csv_log(final_job_output,timestamp)

                        #drop the link and the time off the screen output
                        del final_job_output[0]
                        del final_job_output[0]

                        print(f"      data: {final_job_output}")
                    else:
                        print ("ERROR: something happened with the above job when we asked chatgpt to parse the info")
                else:
                    print ("ERROR: something happened with the above job in when we tried to get the job description")
        else:
            print ("ERROR: something happened with the above rss feed when we tried to download it")
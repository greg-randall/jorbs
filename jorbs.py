import time
import urllib


from jorbs_config import * #make sure to copy and rename 'jorbs_config_blank.py' to  'jorbs_config.py'
from jorbs_functions import *


timestamp = int(time.time()) #have a conistent timestamp for all of the logging from the start of the run

aggregators_rss_url = []
for aggregator in aggregators_rss:
    print(f"feed: {aggregator}")
    for keyword in search_keywords:
        print(f"\tkeyword: {keyword}")

        keyword_encded = urllib.parse.quote_plus(keyword) #urlencode the search string -- ie spaces turn to %20, quotes to %22.
        
        url = f"{aggregator}{keyword_encded}" #build the url for collection 

        feed_raw = get_feed(url)
        write_log_item("jorbs_feeds",aggregator,keyword,timestamp,feed_raw) #logging the feeds for later troubleshooting

        job_links = get_links_from_feed(feed_raw) #get the links from the feed

        for job_link in job_links:
            print(f"\t\tjob: {job_link}")

            job_description = get_jorb( job_link ) #collect the page with the job description
            write_log_item("jorbs_jobs",job_link,keyword,timestamp,job_description)  #logging the description for later troubleshooting

            read_job = gpt_jorb_parse(gpt_base_prompt,job_description,open_ai_key)

            final_job_output = split_gpt(read_job,job_link)
            print(f"\t\t\tjob data: {final_job_output}")

            write_jorb_csv_log(final_job_output,timestamp)
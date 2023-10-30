# jorbs
This tool collect jobs from several job aggregators via RSS using keywords and then uses ChatGPT to collect information about the jobs and determine if they're relevant to your job search.

To get things running, clone the repo, duplicate the 'jorbs_config_blank.py' file and rename it to 'jorbs_config.py'. There are instructions about what to change in the config file to search for your desired job.

To start out with, I would comment out line 90 in 'jorbs.py' -- "send_text(phone_number,message,textbelt_key)" or don't enter a textbelt api key in the config file. Then run the tool a few times allowing it to collect all the current jobs. Review those jobs in the generated CSV file, and then once it isn't giving you new jobs every run, enable the text messages, and setup a cronjob to run the script once a day and it'll text you when there are new jobs that meet your paramters. 

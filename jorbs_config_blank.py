open_ai_key = "....."

#aggregators, format so that the keyword part is at the end
aggregators_rss = [
    "https://careers.insidehighered.com/jobsrss/?countrycode=US&keywords=",
    "https://www.timeshighereducation.com/unijobs/jobsrss/?keywords=",
    "https://main.hercjobs.org/jobs/?display=rss&keywords=",
    "https://jobs.chronicle.com/jobsrss/?countrycode=US&keywords=",
    "http://rss.indeed.com/rss?q=",
    #"https://www.acad.jobs/rss/rss.php?cnt=us&cat=268,253,254,263,256,272,273,290,292,293,294,274,275&st=1&ju=1&se=1&a=1&p=1&q=",
    ]

#search keywords, add in double quotes as needed, tho note site support might differ somewhat, possibly ignoring quotes
search_keywords = [
    '"web developer"',
    'fullstack',
    ]


gpt_base_prompt = '''\
    Please read the job description below.

    Determine if the job is related web development, answer TRUE or FALSE.
    Output a linebreak.
    Find pay information, reply with a dollar amount otherwise answer FALSE.
    Output a linebreak.
    Determine if the location of the job, answer in the form of CITY, STATE, if the answer isn't in the form of 'CITY, STATE' answer FALSE.

    
    Job Description:
    '''
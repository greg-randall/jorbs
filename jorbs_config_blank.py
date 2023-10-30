open_ai_key = "....."

textbelt_key = "....."

phone_number = "....."

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

#so this is a new way of doing chatgpt prompts to get structured information out.
#below you see several items under 'properties' for example:
#   'summary': {
#        'type': 'string',
#        'description': 'Two sentence job summary',
#this defines something that you want in your output, 
# #you need to name the part, 'summary' here, 
# type will typically be 'string', 
# and then under description breifly say what the variable should contain
#
#below you'll notice we have several types, there's a true or false for 'full-time-job' and
#an integer for pay information

#please note as you add and remove items under 'properties', you should add the items's name under 'required' at the very bottom

functions = [
    {
        'name': 'get_job_information',
        'description': 'Get information from a job description including job title, job summary, job requirements, if the job is bookarts related, if the job is full time.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job-title': {
                    'type': 'string',
                    'description': 'Job title',
                },
                'summary': {
                    'type': 'string',
                    'description': 'Two sentence job summary',
                },
                'requirements': {
                    'type': 'string',
                    'description': 'Two sentence job requirements',
                },
                'full-time-job': {
                    'type': 'string',
                    'description': 'Is the job full-time?',
                    'enum': [
                        'TRUE',
                        'FALSE',
                    ],
                },
                'pay-information': {
                    'type': 'integer',
                    'description': 'Pay information for the job'
                },
            },
            'required': [
                'job-title',
                'summary',
                'requirements',
                'full-time-job',
                'pay-information'
            ],
        },
    },
]
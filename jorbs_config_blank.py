###########SETUP NOTES###########
#add your open ai key, textbelt key, and your phone number below
#add aggregators or remove if they aren't relevant to your job searches (if you find more aggregators, please make a pullrequest)
#add keywords
#edit the functions variable, there are notes about how to make that work below
#finally edit the followup fieldname and relevance question at the very bottom




open_ai_key = "..."
textbelt_key = "..."
phone_number = "..."



#aggregators, format so that the keyword part is at the end
#note: if you add aggregators go read the get_jorb function in the functions file, there's some per-site cleanup that happens
aggregators_rss = [
    "https://jobs.chronicle.com/jobsrss/?countrycode=US&keywords=",
    "https://careers.insidehighered.com/jobsrss/?countrycode=US&keywords=",
    "https://www.timeshighereducation.com/unijobs/jobsrss/?keywords=",
    "https://main.hercjobs.org/jobs/?display=rss&keywords=",
    "http://rss.indeed.com/rss?q=",
]



#search keywords, add in double quotes as needed, tho note site support might differ somewhat, possibly ignoring quotes
search_keywords = [
    'letterpress',
    '"book arts"',
    '"artist books"',
    '"artist\'s books"',
    '"book binding"',
    'bookbinding',
    '"book conservation"',
    'papermaking',
    'bookbinder',
    '"book conservator"',
    '"fine press"',
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
#DO NOT remove the Requirements and Summary field, they are used in the relevance field at the bottom of this file.
functions = [
    {
        'name': 'get_job_information',
        'description': 'Get information from a job description including job title, job summary, job requirements, if the job is bookarts related, if the job is full time, etc.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job-location': {
                    'type': 'string',
                    'description': 'Job location, ie City, State',
                },
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
                    'description': 'Two sentence job requirements summary',
                },
                'full-time-job-bool': {
                    'type': 'string',
                    'description': 'Is the job full-time?',
                    'enum': [
                        'TRUE',
                        'FALSE',
                    ],
                },
                'mfa-required-bool': {
                    'type': 'string',
                    'description': 'Is a masters in fine arts (MFA) degree required?',
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
                'full-time-job-bool',
                'pay-information',
                'job-location',
                'mfa-required-bool'
            ],
        },
    },
]


#this asks a followup question of chatgpt to determine if the job is relevant to your search (your above keywords might not actually get you relevant jobs)
#the field name is the column name that will come out in the output CSV and screen log
#relevance is the actual question you want to ask chatgpt. this only uses the job summary and job requirements summary from the previous chatgpt question, so it's
#pretty cheap. the summary and requirements are automatically appened to the end of the relevance field.
#keep the end part "Reply with TRUE or FALSE." we are going to usue true or false to determine if we should text you or not
relevance_field_name = "bookarts"
relevance = "Read the job description and job requiremtns below and determine if this job is related to bookarts, letterpress or bookbinding. Reply with TRUE or FALSE."
import openai
from openai import OpenAI
from datetime import datetime
from typing import Optional
import sys
import os
import json
from requests_cache import CachedSession

# monkey patch cache fuckery
new_cache_path = '/tmp/cache/kerykeion_geonames_cache'
os.makedirs(new_cache_path, exist_ok=True)
original_init = CachedSession.__init__

def patched_init(self, *args, **kwargs):
    kwargs['cache_name'] = new_cache_path
    original_init(self, *args, **kwargs)

CachedSession.__init__ = patched_init

from kerykeion import AstrologicalSubject, Report

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.")
    except IOError:
        print(f"Error: An error occurred while reading the file at '{file_path}'.")
        
def inject_variables(template_string, **kwargs):
    try:
        formatted_string = template_string.format(**kwargs)
        return formatted_string
    except KeyError as e:
        print(f"Error: Missing key {e} in format string.")
        return None
    
def create_chat_completion(client, prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages = [{"role": "user", "content": prompt}],
            max_tokens=500,
            n=1,
            temperature=0.68,
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def create_astro_subject(year: int, month: int, day:int,
                         name_id: str =  "user", 
                         hour: int = 0, minute: int = 0,
                         city: str = "Houston") -> Optional[AstrologicalSubject]:
    try:
        subject = AstrologicalSubject(name_id, year, month, day, 0, 0, "Houston")
        return subject
    except Exception as e:
        print(f"cannot create astrological subject object: {e}")
        return None
    
def get_subject_zodiac_sign(subject: AstrologicalSubject) -> Optional[str]:
    try:
        result = subject.sun.sign
        if result is not None:
            return result
        else:
            print("no zodiac sign can be found from the subject")
            return None
    except Exception as e:
        print(f"cannot get zodiac sign: {e}")
        return None

def get_subject_chart_report(subject: AstrologicalSubject) -> Optional[str]:
    try: 
        report = Report(subject)
        return report
    except Exception as e:
        print(f"cannot get chart report: {e}")
        return None
        
def lambda_handler(event, context):
    try:
        year = event['queryStringParameters'].get('year')
        month = event['queryStringParameters'].get('month')
        day = event['queryStringParameters'].get('date')
        
        if year is not None:
            year = int(year)
        else:
            year = 1998
            
        if month is not None:
            month = int(month)
        else:
            month = 6
            
        if day is not None:
            day = int(day)
        else:
            day = 21
        
        main_subj = create_astro_subject(year = year, month = month, day=day)

        # deterministic part
        zodiac_sign = get_subject_zodiac_sign(main_subj)
        chart_report = get_subject_chart_report(main_subj)
        
        # gpt
        now_date = str(datetime.now())[:10]
        prompt = read_file("prompt.txt")
        prompt_args = {'date': now_date, 'zodiac': zodiac_sign}
        prompt_fmt = inject_variables(prompt, **prompt_args)
        
        ## gpt make calls
        OAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        oai_client = OpenAI(api_key=OAI_API_KEY)
        gpt_horoscope = create_chat_completion(client=oai_client, prompt=prompt_fmt)
        
        # render output
        result = {"sign": zodiac_sign,
                "charts": chart_report.get_full_report(),
                "horoscope": gpt_horoscope}
        
        result_lambda = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
        
        return result_lambda
    except Exception as e:
        print(f"API call failed: {e}")
        result_lambda = {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': "you messed up something bruh"
        }
        
        return result



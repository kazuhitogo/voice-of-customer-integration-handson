import boto3
import os
import logging
import time
import json
from urllib.request import urlopen
import string
from common_lib import find_duplicate_person, id_generator

# Log level
logging.basicConfig()
logger = logging.getLogger()
if os.getenv('LOG_LEVEL') == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Parameters
REGION = os.getenv('AWS_REGION')
# Check valid languages here: https://docs.aws.amazon.com/comprehend/latest/dg/API_BatchDetectEntities.html#comprehend-BatchDetectEntities-request-LanguageCode
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', default="ja")

comprehend = boto3.client(service_name='comprehend', region_name=REGION)

commonDict = {'i': 'I'}

s3_client = boto3.client("s3")

# Pull the bucket name from the environment variable set in the cloudformation stack
BUCKET = os.environ['BUCKET_NAME']

def detect_all(text):
    retval = {}
    comprehend = boto3.client(service_name='comprehend', region_name=REGION)
    # 感情分析
    res = comprehend.detect_sentiment(Text=text,LanguageCode=LANGUAGE_CODE)
    retval['Positive'] = res['SentimentScore']['Positive']
    retval['Negative'] = res['SentimentScore']['Negative']
    retval['Neutral'] = res['SentimentScore']['Neutral']
    retval['Mixed'] = res['SentimentScore']['Mixed']
    retval['sentiment'] = res['Sentiment']
    # キーフレーズ
    res = comprehend.detect_key_phrases(Text=text,LanguageCode=LANGUAGE_CODE)
    retval['KeyPhrases'] = []
    if res['KeyPhrases'] == []:
        pass
    else:
        for r in res['KeyPhrases']:
            retval['KeyPhrases'].append(r['Text'])
    # エンティティ
    res = comprehend.detect_entities(Text=text,LanguageCode=LANGUAGE_CODE)
    retval['Entities'] = []
    if res['Entities'] == []:
        pass
    else:
        for r in res['Entities']:
            retval['Entities'].append(r['Text'])
    return retval

def process_transcript(transcription_url,agent_name='',agent_arn=''):
    custom_vocabs = None

    response = urlopen(transcription_url)
    output = response.read()
    json_data = json.loads(output)
    logger.info(json_data)

    # customer
    customer_transcriptions = []
    # センテンスを作成する
    # 1 秒未満に続いた単語は同じセンテンスとし、1 秒以上空いた音声は別センテンスとする
    for d in json_data['results']['channel_labels']['channels'][0]['items']:
        if 'start_time' not in d:
            pass
        elif customer_transcriptions == [] or float(d['start_time']) - float(customer_transcriptions[-1]['end_time']) >= 1:
            customer_transcriptions.append({
                'job_name':json_data['jobName'],
                'person':'customer',
                'start_time':d['start_time'],
                'end_time':d['end_time'],
                'content':d['alternatives'][0]['content'],
                'detail_flag':True
            })
        elif float(d['start_time']) - float(customer_transcriptions[-1]['end_time']) < 1: # 1秒未満
            customer_transcriptions[-1]['end_time'] = d['end_time']
            customer_transcriptions[-1]['content'] += d['alternatives'][0]['content']
    
    for customer_transcription in customer_transcriptions:
        customer_transcription['start_time'] = int(float(customer_transcription['start_time'])*1000)
        customer_transcription['end_time'] = int(float(customer_transcription['end_time'])*1000)
    for i,customer_transcription in enumerate(customer_transcriptions):
        customer_result = detect_all(customer_transcription['content'])
        # res = comprehend.detect_sentiment(Text=customer_transcription['content'],LanguageCode=LANGUAGE_CODE)
        for key in customer_result.keys():
            customer_transcriptions[i][key] = customer_result[key]

    # agent
    agent_transcriptions = []
    # センテンスを作成する
    # 1 秒未満に続いた単語は同じセンテンスとし、1 秒以上空いた音声は別センテンスとする
    for d in json_data['results']['channel_labels']['channels'][1]['items']:
        if 'start_time' not in d:
            pass
        elif agent_transcriptions == [] or float(d['start_time']) - float(agent_transcriptions[-1]['end_time']) >= 1:
            agent_transcriptions.append({
                'job_name':json_data['jobName'],
                'person':'agent',
                'start_time':d['start_time'],
                'end_time':d['end_time'],
                'content':d['alternatives'][0]['content'],
                'agent_arn':agent_arn,
                'agent_name':agent_name,
                'detail_flag':True
            })
        elif float(d['end_time']) - float(agent_transcriptions[-1]['end_time']) < 1:
            agent_transcriptions[-1]['end_time'] = d['end_time']
            agent_transcriptions[-1]['content'] += d['alternatives'][0]['content']
    for agent_transcription in agent_transcriptions:
        agent_transcription['start_time'] = int(float(agent_transcription['start_time'])*1000)
        agent_transcription['end_time'] = int(float(agent_transcription['end_time'])*1000)
    for i,agent_transcription in enumerate(agent_transcriptions):
        agent_result = detect_all(agent_transcription['content'])
        # res = comprehend.detect_sentiment(Text=agent_transcription['content'],LanguageCode=LANGUAGE_CODE)
        for key in agent_result.keys():
            agent_transcriptions[i][key] = agent_result[key]
    
    # 全体のtranscription
    ## agent
    agent_content = ''
    for item in json_data['results']['channel_labels']['channels'][1]['items']:
        agent_content += item['alternatives'][0]['content']
    agent_content = agent_content.replace(' ','')
    ## customer
    customer_content = ''
    for item in json_data['results']['channel_labels']['channels'][0]['items']:
        customer_content += item['alternatives'][0]['content']
    customer_content = customer_content.replace(' ','')
    ## whole
    whole_transcription = {
        'whole_transcript': json_data['results']['transcripts'][0]['transcript'].replace(' ',''),
        'agent_transcript': agent_content,
        'customer_transcript': customer_content,
        'job_name':json_data['jobName'],
        'agent_arn':agent_arn,
        'agent_name':agent_name,
        'detail_flag':False,
    }
    whole_detect_result = detect_all(whole_transcription['whole_transcript'])
    for key in whole_detect_result.keys():
        whole_transcription['whole_'+key]=whole_detect_result[key]
    
    agent_detect_result = detect_all(whole_transcription['agent_transcript'])
    for key in agent_detect_result.keys():
        whole_transcription['agent_'+key]=agent_detect_result[key]
    
    customer_detect_result = detect_all(whole_transcription['customer_transcript'])
    for key in customer_detect_result.keys():
        whole_transcription['customer_'+key]=customer_detect_result[key]
    
    
    
    # s3upload
    transcript_locations = []

    # customer
    for customer_transcription in customer_transcriptions:
        key = 'callrecords/transcript/sentence/customer/' + id_generator() + '.json'
        response = s3_client.put_object(Body=json.dumps(customer_transcription, indent=2), Bucket=BUCKET, Key=key)
        logger.info(json.dumps(response, indent=2))
        logger.info("successfully written transcript to s3://" + BUCKET + "/" + key)
    
        # Return the bucket and key of the transcription / comprehend result.
        transcript_locations.append({"bucket": BUCKET, "key": key})
    # agent
    for agent_transcription in agent_transcriptions:
        key = 'callrecords/transcript/sentence/agent/' + id_generator() + '.json'
        response = s3_client.put_object(Body=json.dumps(agent_transcription, indent=2), Bucket=BUCKET, Key=key)
        logger.info(json.dumps(response, indent=2))
        logger.info("successfully written transcript to s3://" + BUCKET + "/" + key)
    
        # Return the bucket and key of the transcription / comprehend result.
        transcript_locations.append({"bucket": BUCKET, "key": key})
    # コール全体のjson保存
    key = 'callrecords/transcript/whole/json/' + id_generator() + '.json'
    response = s3_client.put_object(Body=json.dumps(whole_transcription, indent=2), Bucket=BUCKET, Key=key)
    logger.info(json.dumps(response, indent=2))
    logger.info("successfully written transcript to s3://" + BUCKET + "/" + key)
    transcript_locations.append({"bucket": BUCKET, "key": key})
    
    
    logger.info('return value:')
    logger.info(transcript_locations)
    return transcript_locations

def lambda_handler(event, context):
    """
        AWS Lambda handler
    """
    logger.info('Received event')
    logger.info(json.dumps(event))

    # Pull the signed URL for the payload of the transcription job
    transcription_url = event['transcribeStatus']['transcriptionUrl']

    return process_transcript(transcription_url)

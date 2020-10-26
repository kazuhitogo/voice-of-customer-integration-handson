import boto3
import certifi
import json
import os
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import logging

# Log level
logging.basicConfig()
logger = logging.getLogger()

# Parameters
REGION = os.getenv('AWS_REGION')
esendpoint = os.environ['ES_DOMAIN']
FULL_EPISODE_INDEX = os.getenv('ES_EPISODE_INDEX', default='call-transcript')
SENTENCE_INDEX = os.getenv('ES_SENTENCE_INDEX', default='detail-call-transcript')
FULL_EPISODE_DOCTYPE = os.getenv('FULL_EPISODE_DOCTYPE', default='doc')

s3_client = boto3.client('s3')
# Create the auth token for the sigv4 signature
session = boto3.session.Session()
credentials = session.get_credentials().get_frozen_credentials()
awsauth = AWSRequestsAuth(
    aws_access_key=credentials.access_key,
    aws_secret_access_key=credentials.secret_key,
    aws_token=credentials.token,
    aws_host=esendpoint,
    aws_region=REGION,
    aws_service='es'
)

# Connect to the elasticsearch cluster using aws authentication. The lambda function
# must have access in an IAM policy to the ES cluster.
es = Elasticsearch(
    hosts=[{'host': esendpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ca_certs=certifi.where(),
    timeout=120,
    connection_class=RequestsHttpConnection
)


# Entry point into the lambda function
def lambda_handler(event, context):
    print('event:')
    print(event)
    print('context:')
    print(context)
    fullEpisodeS3Locations = event["processedTranscription"][0]
    for i,fullEpisodeS3Location in enumerate(fullEpisodeS3Locations):
        contact_id = event['key'].split('/')[-1].split('_')[0] + '-' +str(i).zfill(5)
        index_episode(es, event, fullEpisodeS3Location,contact_id)
    return


def index_episode(es, event, fullEpisodeS3Location,contactId):
    response = s3_client.get_object(Bucket=fullEpisodeS3Location['bucket'], Key=fullEpisodeS3Location['key'])
    file_content = response['Body'].read().decode('utf-8')
    fullepisode = json.loads(file_content)

    s3_location = "s3://" + event['bucket'] + "/" + event['key']

    s = event['key'].split('_')[1]

    contact_id = contactId

    updateDoc = {
        'doc':{
            'audio_type': event['audio_type'],
            'audio_s3_location': s3_location,
            'contact_id': contact_id,
            'LastUpdateTimestamp': s[0:4] + '-' + s[4:6] + '-' + s[6:8] + 'T' + s.split('T')[1] + 'Z',
            'type': 'CallRecord',
            'wavfile_name': event['key'].split('/')[-1]
        },
        "doc_as_upsert" : True
    }
    for key in fullepisode.keys():
        updateDoc['doc'][key] = fullepisode[key]

    es.update(
        index=SENTENCE_INDEX + '-' + s[0:4] + '-' + s[4:6] + '-' + s[6:8] if fullepisode['detail_flag'] == True else FULL_EPISODE_INDEX + '-'  + s[0:4] + '-' + s[4:6] + '-' + s[6:8],
        doc_type=FULL_EPISODE_DOCTYPE,
        body=updateDoc,
        id=contact_id
        )

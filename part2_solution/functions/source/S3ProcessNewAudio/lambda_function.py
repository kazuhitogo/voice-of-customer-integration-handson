import json
import urllib.request, urllib.parse, urllib.error
import boto3
import os

print('Loading function')

s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

stepfunctionsarn = os.getenv('STEP_FUNCTIONS_ARN')

def lambda_handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    try:
        response = stepfunctions.start_execution(
                stateMachineArn=stepfunctionsarn,
                input=str(json.dumps({
                    "dryrun": False,
                    "audio_type": "audio/wav",
                    "bucket": bucket,
                    "key": key
                     })))
        
        print(f'kicked off state machine for {bucket}/{key}')
        
        return 'true'
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

import boto3
import random
import string
import http.client
from urllib.parse import urlparse
import json
import os

es_client = boto3.client('es')
cognito_idp_client = boto3.client('cognito-idp')
step_function_client = boto3.client('stepfunctions')
s3_client = boto3.client('s3')

# Generates a random ID for the step function execution
def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))     

def pwd_generator(size=8):
    lowerChars = string.ascii_lowercase
    upperChars = string.ascii_uppercase
    digits = string.digits
    specials = '%$#&[]'
    return random.choice(lowerChars) + random.choice(upperChars) + random.choice(digits) + random.choice(specials) + random.choice(lowerChars) + random.choice(upperChars) + random.choice(digits) + random.choice(specials) 


def lambda_handler(event, context):
    try:
        return process_cfn(event, context)
    except Exception as e:
        print(("EXCEPTION", e))
        print(e)
        send_response(event, {
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId']
            }, "FAILED")

def process_cfn(event, context):
    print(("Received event: " + json.dumps(event, indent=2)))
    
    stepFunctionArn = os.environ['STEP_FUNCTION_ARN']

    esDomainName = event['ResourceProperties']['esCluster']
    userPoolId = event['ResourceProperties']['UserPoolId']
    identityPoolId = event['ResourceProperties']['IdentityPoolId']
    esRoleArn = event['ResourceProperties']['esRoleArn']

    kibanaUser = event.get('ResourceProperties', {}).get('kibanaUser', 'kibana')

    if 'kibanaEmail' in event['ResourceProperties'] and event['ResourceProperties']['kibanaEmail'] != '':
        kibanaEmail = event['ResourceProperties']['kibanaEmail']
    else:
        kibanaEmail = id_generator(6) + '@example.com'

    kibanaPassword = pwd_generator()

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'IN_PROCESS',
        'kibanaPassword': kibanaPassword,
        'kibanaUser': kibanaUser
    }

    if 'PhysicalResourceId' in event:
        response['PhysicalResourceId'] = event['PhysicalResourceId']
    else:
        response['PhysicalResourceId'] = esDomainName + '-cognito'

    if event['RequestType'] == 'Delete':
        try:
            cognito_idp_client.delete_user_pool_domain(
                Domain=esDomainName,
                UserPoolId=userPoolId
            )
        except cognito_idp_client.exceptions.InvalidParameterException:
            pass
        

        send_response(event, response, status="SUCCESS", reason="User Pool Domain Deleted")
        return


    add_user(userPoolId, kibanaUser, kibanaEmail, kibanaPassword)

    print(("ES Domain : " + esDomainName + "\tUserPool:" + userPoolId))

    try:
        cognito_idp_client.create_user_pool_domain(
            Domain=esDomainName,
            UserPoolId=userPoolId
        )
    except cognito_idp_client.exceptions.InvalidParameterException:
        pass

    cognitoOptions = {
        "Enabled": True,
        "UserPoolId": userPoolId,
        "IdentityPoolId": identityPoolId,
        "RoleArn": esRoleArn
    }

    try:
        es_client.update_elasticsearch_domain_config(
            DomainName=esDomainName,
            CognitoOptions=cognitoOptions)
    except:
        pass
        
    response["DomainName"] = esDomainName

    stepFunctionPayload = {"event": event, "response": response}
    step_function_client.start_execution(
        stateMachineArn=stepFunctionArn,
        name=id_generator(),
        input=json.dumps(stepFunctionPayload, indent=4, sort_keys=True, default=str)
    )
    return stepFunctionPayload

def add_user(userPoolId, kibanaUser, kibanaEmail, kibanaPassword):
    cognito_response = cognito_idp_client.admin_create_user(
        UserPoolId=userPoolId,
        Username=kibanaUser,
        UserAttributes=[
            {
                'Name': 'email',
                'Value': kibanaEmail
            },
            {
                'Name': 'email_verified',
                'Value': 'True'
            }
        ],
        TemporaryPassword=kibanaPassword,
        MessageAction='SUPPRESS',
        DesiredDeliveryMediums=[
            'EMAIL'
        ]
    )
    return cognito_response

def send_response(request, response, status=None, reason=None):
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    if not 'PhysicalResourceId' in response or response['PhysicalResourceId']:
        response['PhysicalResourceId'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse(request['ResponseURL'])
        body = json.dumps(response)
        https = http.client.HTTPSConnection(url.hostname)
        https.request('PUT', url.path+'?'+url.query, body)

    return response

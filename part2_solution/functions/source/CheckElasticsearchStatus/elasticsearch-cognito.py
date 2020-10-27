import boto3
import random
import string
import http.client
import urllib.parse
import json

es_client = boto3.client('es')
s3_client = boto3.client('s3')

def send_response(request, response, status=None, reason=None):
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    if not 'PhysicalResourceId' in response or response['PhysicalResourceId']:
        response['PhysicalResourceId'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urllib.parse.urlparse(request['ResponseURL'])
        body = json.dumps(response)
        print(('body', url, body))
        https = http.client.HTTPSConnection(url.hostname)
        https.request('PUT', url.path+'?'+url.query, body)

    return response

def check_status(event, context):
    print(("Received event: " + json.dumps(event, indent=2)))

    if "IsFail" in event["event"]:
        send_response(event["event"], {}, status="FAILED", reason="Forced Error")
        return


    if event["event"]["RequestType"] == "Delete":
        try:
            es_response = es_client.describe_elasticsearch_domain(DomainName=event["response"]["PhysicalResourceId"])


        except es_client.exceptions.ResourceNotFoundException:
            print('Domain not found - delete Successful')

            event["response"]["Status"] = "SUCCESS"
            event["response"]['Reason'] = 'Successful'

            if event["event"]["ResponseURL"] == '':
                s3params = {"Bucket": 'gillemi-gillemi', "Key": 'result.json'}
                event["event"]["ResponseURL"] = s3_client.generate_presigned_url('put_object', s3params)
                print(('The URL is', event["event"]["ResponseURL"]))

            send_response(event["event"], event["response"])

        return event

    es_response = es_client.describe_elasticsearch_domain(DomainName=event["response"]["DomainName"])

    if es_response["DomainStatus"]["Processing"] == False and 'Endpoint' in es_response["DomainStatus"]:
        event["response"]["Status"] = "SUCCESS"
        event["response"]["Data"]   = {
            "DomainName": event["response"]["DomainName"],
            "Endpoint":  es_response["DomainStatus"]["Endpoint"],
            "KibanaUser": event["response"]["kibanaUser"],
            "KibanaPassword": event["response"]["kibanaPassword"]
        }
        event["response"]['Reason'] = 'Successful'

        send_response(event["event"], event["response"])

    return event

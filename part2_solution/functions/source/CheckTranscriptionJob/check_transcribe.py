import boto3,json

# The entry point for the lambda function
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    transcribeJob = event['transcribeJob']
    client = boto3.client('transcribe')

    # Call the AWS SDK to get the status of the transcription job
    transcribe_response = client.get_transcription_job(TranscriptionJobName=transcribeJob)

    # Pull the transcribe job status
    transcribe_job_status = transcribe_response['TranscriptionJob']['TranscriptionJobStatus']

    retval = {
        "status": transcribe_job_status
    }

    # If the status is completed, return the transcription file url. This will be a signed url
    # that will provide the full details on the transcription
    if transcribe_job_status == 'COMPLETED':
        retval["transcriptionUrl"] = transcribe_response['TranscriptionJob']['Transcript']['TranscriptFileUri']

    print(retval)

    return retval

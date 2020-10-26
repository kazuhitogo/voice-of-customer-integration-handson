
import boto3
import json
import datetime
from time import mktime
import os
from common_lib import id_generator
import logging
from botocore.config import Config

# Log level
logging.basicConfig()
logger = logging.getLogger()

class ThrottlingException(Exception):
    pass

CONTENT_TYPE_TO_MEDIA_FORMAT = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/flac": "flac",
    "audio/mp4a-latm": "mp4"}

# Check valid language codes here: https://docs.aws.amazon.com/transcribe/latest/dg/API_StartTranscriptionJob.html#transcribe-StartTranscriptionJob-request-LanguageCode
# Note that you should also check the valid languages in AWS Comprehend. If you choose to transcribe in a language
# That is not supported by AWS Comprehend, the comprehension analysis will not work.
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', default = "ja-JP")


class InvalidInputError(ValueError):
    pass


# Custom encoder for datetime objects
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)


# limit the number of retries submitted by boto3 because Step Functions will handle the exponential retries more efficiently
config = Config(
    retries=dict(
        max_attempts=2
    )
)

client = boto3.client('transcribe', config=config)


# Entrypoint for lambda funciton
def lambda_handler(event, context):
    print("Received event" + json.dumps(event, indent=4))

    session = boto3.session.Session()
    region = session.region_name

    # Default to unsuccessful
    isSuccessful = "FALSE"

    # Create a random name for the transcription job
    jobname = id_generator()

    # Extract the bucket and key from the lambda function
    bucket = event['bucket']
    key = event['key']
    content_type = event['audio_type']
    if content_type not in CONTENT_TYPE_TO_MEDIA_FORMAT:
        raise InvalidInputError(content_type + " is not supported audio type.")

    media_type = CONTENT_TYPE_TO_MEDIA_FORMAT[content_type]
    logger.info("media type: " + content_type)

    # Assemble the url for the object for transcribe. It must be an s3 url in the region
    url = "https://s3-" + region + ".amazonaws.com/" + bucket + "/" + key

    try:
        settings = {
            'ChannelIdentification': True
        }

        print('url: ' + url)

        # Call the AWS SDK to initiate the transcription job.
        response = client.start_transcription_job(
            TranscriptionJobName=jobname,
            LanguageCode=LANGUAGE_CODE,
            Settings=settings,
            MediaFormat=media_type,
            Media={
                'MediaFileUri': url
            }
        )
        isSuccessful = "TRUE"
    except client.exceptions.BadRequestException as e:
        # There is a limit to how many transcribe jobs can run concurrently. If you hit this limit,
        # return unsuccessful and the step function will retry.
        logger.error(str(e))
        raise ThrottlingException(e)
    except client.exceptions.LimitExceededException as e:
        # There is a limit to how many transcribe jobs can run concurrently. If you hit this limit,
        # return unsuccessful and the step function will retry.
        logger.error(str(e))
        raise ThrottlingException(e)
    except client.exceptions.ClientError as e:
        # Return the transcription job and the success code
        # There is a limit to how many transcribe jobs can run concurrently. If you hit this limit,
        # return unsuccessful and the step function will retry.
        logger.error(str(e))
        raise ThrottlingException(e)
    return {
        "success": isSuccessful,
        "transcribeJob": jobname
    }

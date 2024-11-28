import socket
import bson
import hashlib
import datetime
import random
from bson import ObjectId
from publisher1 import publish_to_rabbitmq  # to make messageSender functional


class statusFeed:
    @staticmethod
    def messageBuilder(learnerObjectFile,content_ID, statusMessage, details):
        # Generate IDs and timestamps
        job_id = str(ObjectId())
        content_id = content_ID  # Provided as parameter
        timestamp = datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')

        # Construct the message in the required format
        print("THIS IS NUTS")
        print(content_id)
        job = {
            'time': timestamp,
            'job_id': job_id,
            'content_id': content_id,
            'media_id': "N/A",
            'content_type': 'Status Message',  # Default; adjust as needed
            'file_name': learnerObjectFile,
            'status': statusMessage,
            'message':details,
            '_id': ObjectId()
        }
        print(f"Generated job: {job}")

        # Send back to messageSender
        messageSender(job)


# This sends to our RabbitMQ publisher
def messageSender(job):
    # Send job to RabbitMQ
    publish_to_rabbitmq('.Status.', job)

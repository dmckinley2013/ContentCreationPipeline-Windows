import socket
import bson
import hashlib
import datetime
import random
import logging
from publisher import publish_to_rabbitmq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class statusFeed:
    @staticmethod
    def messageBuilder(content_ID, statusMessage, details):
        print("Inside Message Builder")
        try:
            messageID = str(random.random())
            cts = datetime.datetime.now()
            format_cts = cts.strftime('%m/%d/%Y, %I:%M:%S %p')

            job = {
                "JobID": messageID,
                "contentID": content_ID,
                "Status": statusMessage,
                "time": format_cts,  # Using consistent time format
                "details": details,
                "message": f"Status update for content {content_ID}"
            }
            
            logging.info(f"Built status message for content {content_ID}")
            messageSender(job)
            
        except Exception as e:
            logging.error(f"Error building message: {e}")
            raise

def messageSender(bsonObj):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 12346))
        s.sendall(bson.encode(bsonObj))
        s.close()
        logging.info(f"Status message sent for job {bsonObj.get('JobID')}")
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        raise 
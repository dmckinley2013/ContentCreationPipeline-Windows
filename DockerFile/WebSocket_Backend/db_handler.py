from pymongo import MongoClient
from bson import BSON
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DBHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None

    def init_db(self):
        """Initialize the MongoDB connection."""
        try:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['dashboard_db']
            self.collection = self.db['messages']
            logging.info("Connected to MongoDB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def save_message_to_db(self, message):
        """Save a message to the database."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        job_id = message.get('ID', 'Unknown JobID')
        content_id, content_type = self.get_content_info(message)
        file_name = message.get('FileName', 'Unknown File')
        status = message.get('Status', 'Processed')
        message_text = message.get('Message', 'No additional information')

        document = {
            "time": timestamp,
            "job_id": job_id,
            "content_id": content_id,
            "content_type": content_type,
            "file_name": file_name,
            "status": status,
            "message": message_text
        }

        try:
            self.collection.insert_one(document)
            logging.info(f"Saved message to MongoDB: {document}")
        except Exception as e:
            logging.error(f"Failed to save message to MongoDB: {e}")

    def get_content_info(self, message):
        """Extract content ID and type from the message."""
        if 'DocumentId' in message:
            return message['DocumentId'], 'Document'
        elif 'PictureID' in message:
            return message['PictureID'], 'Picture'
        elif 'AudioID' in message:
            return message['AudioID'], 'Audio'
        elif 'VideoID' in message:
            return message['VideoID'], 'Video'
        else:
            return 'Unknown ContentID', 'Unknown Type'

    def load_messages(self):
        """Load messages from the database."""
        try:
            # Get messages from the collection
            messages = list(self.collection.find().sort("time", -1))
            message_count = len(messages)  # Count the number of messages

            logging.info(f"Loaded {message_count} messages from MongoDB")
            return messages
        except Exception as e:
            logging.error(f"Failed to load messages from MongoDB: {e}")
        return []


# Example usage:
if __name__ == "__main__":
    db_handler = DBHandler()
    db_handler.init_db()
    messages = db_handler.load_messages()
    print(f"Loaded {len(messages)} messages from the database.")

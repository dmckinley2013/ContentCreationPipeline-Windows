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
        """Initialize database connection."""
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
        try:
            # Debug log the incoming message
            logging.info(f"Attempting to save message: {message}")
            
            # If message is BSON, decode it
            if isinstance(message, bytes):
                message = BSON(message).decode()

            # Extract or generate the timestamp
            timestamp = message.get('time')
            if not timestamp:
                timestamp = datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')

            # Create document with proper field mapping
            document = {
                "time": timestamp,
                "job_id": message.get('job_id') or message.get('ID', 'Unknown JobID'),
                "content_id": message.get('content_id'),
                "media_id": (message.get('media_id','Unknown ContentID')),
                "content_type": message.get('content_type') or self._determine_content_type(message),
                "file_name": message.get('file_name') or message.get('FileName', 'Unknown File'),
                "status": message.get('status', 'Processed'),
                "message": message.get('message', 'No additional information')
            }

            # Only save if we have valid data
            if self._is_valid_document(document):
                self.collection.insert_one(document)
                logging.info(f"Successfully saved message to MongoDB: {document}")
            else:
                logging.warning(f"Skipping invalid document: {document}")

        except Exception as e:
            logging.error(f"Failed to save message to MongoDB: {e}")
            raise

    def _determine_content_type(self, message):
        """Determine content type from message structure."""
        if 'DocumentId' in message:
            return 'Document'
        elif 'PictureID' in message:
            return 'Picture'
        elif 'AudioID' in message:
            return 'Audio'
        return message.get('content_type', 'Unknown Type')

    def _is_valid_document(self, document):
        """Check if document has valid data."""
        return (
            document['job_id'] != 'Unknown JobID' or
            document['content_id'] != 'Unknown ContentID' or
            document['content_type'] != 'Unknown Type'
        )

    def load_messages(self):
        """Load messages from the database."""
        try:
            # Get messages and sort by time in descending order
            messages = list(self.collection.find(
                {
                    "$or": [
                        {"job_id": {"$ne": "Unknown JobID"}},
                        {"content_id": {"$ne": "Unknown ContentID"}},
                        {"content_type": {"$ne": "Unknown Type"}}
                    ]
                },
                {'_id': 0}
            ).sort("time", -1))
            
            logging.info(f"Successfully loaded {len(messages)} messages from MongoDB")
            return messages
        except Exception as e:
            logging.error(f"Failed to load messages from MongoDB: {e}")
            return []

    def clear_invalid_messages(self):
        """Clear invalid messages from the database."""
        try:
            result = self.collection.delete_many({
                "$and": [
                    {"job_id": "Unknown JobID"},
                    {"content_id": "Unknown ContentID"},
                    {"content_type": "Unknown Type"}
                ]
            })
            logging.info(f"Cleared {result.deleted_count} invalid messages from MongoDB")
        except Exception as e:
            logging.error(f"Failed to clear invalid messages: {e}")
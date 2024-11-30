import pika
from bson import BSON, decode, encode
import os
import logging
from bson.errors import BSONError



# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.getLogger("pika").setLevel(logging.WARNING)


class MessageProcessor:
    def __init__(self, host="localhost"):
        self.connection_params = pika.ConnectionParameters(
            host, heartbeat=600, blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()

        self.exchange_name = "Topic"
        self.channel.exchange_declare(
            exchange=self.exchange_name, exchange_type="topic", durable=True
        )

        # Define queues
        self.queues = {
            "store": "Store",
            "document": "Document",
            "image": "Image",
        }

        # Declare queues
        for queue_name in self.queues.values():
            self.channel.queue_declare(queue=queue_name, durable=True, arguments=None)

        # Bind queues to the exchange
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queues["store"],
            routing_key="*.Store.*",
        )
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queues["document"],
            routing_key="*.Document.*",
        )
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queues["image"],
            routing_key="*.Image.*",
        )

        self.current_content_id = None
        self.current_folder = None

    @staticmethod
    def create_dir(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Created directory: {directory}")
        return directory

    @staticmethod
    def save_file(file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(data)
            logging.info(f"File saved successfully: {file_path}")
        except Exception as e:
            logging.error(f"Error saving file {file_path}: {str(e)}")

    def process_store(self, ch, method, properties, body, content_id):
        try:
            obj = decode(body)
            message_content_id = obj["content_id"]
            file_name = obj["file_name"]

            # Check if the ContentId matches
            if message_content_id != content_id:
                logging.info(
                    f"Skipping store message with non-matching Content ID: {message_content_id}"
                )
                ch.basic_nack(delivery_tag=method.delivey_tag, requeue=True)
                return

            logging.info(
                f"Received store message with matching ContentId: {content_id}, FileName: {file_name}"
            )

            base_path = self.create_dir(f"store_{content_id}")

            # Save the main payload including original filename
            payload_filename = f"{file_name}+{content_id}+payload.pdf"
            self.save_file(os.path.join(base_path, payload_filename), obj["Payload"])

            # Save Meta, Summary, and Keywords including original filename
            for key in ["Meta", "Summary", "Keywords"]:
                if key in obj:
                    file_filename = f"{file_name}+{content_id}+{key.lower()}.txt"
                    self.save_file(os.path.join(base_path, file_filename), obj[key])
                else:
                    logging.warning(f"Expected key '{key}' not found in store message")

            logging.info(f"Processed store message with ContentId: {content_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except KeyError as e:
            logging.error(f"Missing key in store message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except BSONError as e:
            logging.error("Failed to decode BSON message for store")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logging.error(f"Error processing store message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


    def process_image(self, ch, method, properties, body, content_id):
        try:
            obj = decode(body)
            message_content_id = obj["content_id"]
            file_name = obj["file_name"]

            if message_content_id != content_id:
                logging.info(
                    f"Skipping image with non-matching Content ID: {message_content_id}"
                )
                # Do not send ack; requeue message implicitly by not acking
                return

            # Create or use the directory store_<contentID>
            target_folder = f"store_{content_id}"
            os.makedirs(target_folder, exist_ok=True)

            # Save the file in the target folder
            image_file_name = f"image_{file_name}+{message_content_id}.png"
            self.save_file(os.path.join(target_folder, image_file_name), obj["Payload"])

            logging.info(f"Processed image with Content ID: {message_content_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except KeyError as e:
            logging.error(f"Missing key in image message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logging.error(f"Error processing image message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)




    def consume_image(self, contentID):
        logging.info(f"Starting to consume messages from the Image queue with Content ID: {contentID}")
        
        seen_tags = set()  # To track delivery tags of seen messages
        while True:
            method_frame, properties, body = self.channel.basic_get(queue=self.queues["image"], auto_ack=False)

            if not method_frame:
                logging.info("No more messages in the queue. Stopping consumption.")
                break

            # Detect repetition by checking the delivery tag
            if method_frame.delivery_tag in seen_tags:
                logging.info("Repeated message detected. Stopping consumption.")
                break
            seen_tags.add(method_frame.delivery_tag)

            # Process the message
            try:
                self.process_image(self.channel, method_frame, properties, body, contentID)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                # You can optionally nack here, requeue if needed
                self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                continue


    def consume_store(self, content_id):
        logging.info(f"Starting to consume messages from the Store queue with Content ID: {content_id}")

        def callback(ch, method, properties, body):
            self.process_store(ch, method, properties, body, content_id)
            # Check if the queue is empty after processing
            queue_state = self.channel.queue_declare(queue=self.queues["store"], passive=True)
            if queue_state.method.message_count == 0:
                logging.info("No more messages in the Store queue. Stopping consumption.")
                self.channel.stop_consuming()

        # Consume messages with the callback
        self.channel.basic_consume(
            queue=self.queues["store"],
            on_message_callback=callback,
        )
        self.channel.start_consuming()



if __name__ == "__main__":
    processor = MessageProcessor()

    # Example usage: consume from the Store queue
    processor.consume_image()

    # Example usage: consume from the Image queue
    # processor.consume_image()

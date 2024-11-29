import os
import io
import torch
import torch.nn.functional as F
from PIL import Image
import pika
from bson import decode, decode_all, BSON
import logging
from transformers import AutoModelForImageClassification, AutoImageProcessor


class ImageClassifier:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)

        # Initialize model properties
        self.model_name = "microsoft/resnet-50"
        self.file_path = os.path.dirname(__file__)

        # Queue mapping
        self.queues = {"image": "Image"}

        # Load model and preprocessor
        self.load_model()

        # RabbitMQ setup
        self.setup_rabbitmq()

    def load_model(self):
        try:
            self.model = AutoModelForImageClassification.from_pretrained(
                self.model_name
            )
            self.preprocessor = AutoImageProcessor.from_pretrained(self.model_name)
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise

    def setup_rabbitmq(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()
            for queue in self.queues.values():
                self.channel.queue_declare(queue=queue, durable=True)
            logging.info("RabbitMQ connection established")
        except Exception as e:
            logging.error(f"Error setting up RabbitMQ: {e}")
            raise

    # def classify_image(self, image_data):
    #     try:
    #         image = Image.open(io.BytesIO(image_data)).convert("RGB")
    #         inputs = self.preprocessor(images=image, return_tensors="pt")

    #         with torch.no_grad():
    #             outputs = self.model(**inputs)

    #         logits = outputs.logits
    #         predicted_class_indices = torch.argmax(logits, dim=-1).tolist()
    #         predicted_class = self.model.config.id2label[predicted_class_indices[0]]
    #         confidence_score = F.softmax(logits, dim=-1)[
    #             0, predicted_class_indices[0]
    #         ].item()

    #         logging.info(f"Predicted class: {predicted_class}")
    #         logging.info(f"Confidence score: {confidence_score:.2f}")
    #         return predicted_class, confidence_score
    #     except Exception as e:
    #         logging.error(f"Error in classification: {e}")
    #         raise

    def save_file(self, path, data):
        with open(path, "wb") as f:
            f.write(data)

    def classify_images(self, ch, method, properties, body, content_id):
        try:
            obj = decode(body)
            message_content_id = obj["content_id"]
            file_name = obj["file_name"]
            image_data = obj["Payload"]

            if message_content_id != content_id:
                logging.info(
                    f"Skipping image with non-matching Content ID: {message_content_id}"
                )
                # Do not send ack; requeue message implicitly by not acking
                return

            # Create or use the directory store_<contentID>
            target_folder = f"store_{content_id}"
            os.makedirs(target_folder, exist_ok=True)

            # Process and classify image
            try:
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                inputs = self.preprocessor(images=image, return_tensors="pt")

                with torch.no_grad():
                    outputs = self.model(**inputs)

                logits = outputs.logits
                predicted_class_indices = torch.argmax(logits, dim=-1).tolist()
                predicted_class = self.model.config.id2label[predicted_class_indices[0]]
                confidence_score = F.softmax(logits, dim=-1)[
                    0, predicted_class_indices[0]
                ].item()

                logging.info(
                    f"Classification results - Class: {predicted_class}, Confidence: {confidence_score:.2f}"
                )
            except Exception as e:
                logging.error(f"Error in classification: {e}")
                raise

            # Save the file in the target folder
            image_file_name = f"image_{file_name}+{message_content_id}.png"
            self.save_file(os.path.join(target_folder, image_file_name), image_data)

            # Add classification results to log message
            logging.info(
                f"Processed image with Content ID: {message_content_id}, Class: {predicted_class}"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except KeyError as e:
            logging.error(f"Missing key in image message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logging.error(f"Error processing image message: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def consume_image(self, contentID):
        logging.info(
            f"Starting to consume messages from the Image queue with Content ID: {contentID}"
        )

        seen_tags = set()  # To track delivery tags of seen messages
        while True:
            method_frame, properties, body = self.channel.basic_get(
                queue=self.queues["image"], auto_ack=False
            )

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
                self.classify_images(
                    self.channel, method_frame, properties, body, contentID
                )
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                # You can optionally nack here, requeue if needed
                self.channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                continue

    def cleanup(self):
        try:
            if hasattr(self, "channel") and self.channel.is_open:
                self.channel.close()
            if hasattr(self, "connection") and not self.connection.is_closed:
                self.connection.close()
            logging.info("Cleaned up connections")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def run(self):
        try:
            content_id = input("Enter content ID to process: ")
            self.consume_image(content_id)
        except KeyboardInterrupt:
            logging.info("Shutting down gracefully...")
        except Exception as e:
            logging.error(f"Error in run: {e}")
        finally:
            self.cleanup()


def main():
    classifier = ImageClassifier()
    classifier.run()


if __name__ == "__main__":
    main()

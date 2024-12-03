import os
import io
import torch
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
from PIL import Image
import pika
import logging
from bson import decode
from dbOperationsLocal import nodeBuilder
from statusfeed import statusFeed
class ImageClassifier:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)

        # Model and preprocessor setup
        self.model_name = "mobilenet_v3_large"
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
  # Use Metal backend on macOS
        self.load_model()

        # RabbitMQ setup
        self.queues = {"image": "Image"}
        self.setup_rabbitmq()

    def load_model(self):
        try:
            # Load pretrained weights
            weights = MobileNet_V3_Large_Weights.DEFAULT
            self.model = mobilenet_v3_large(weights=weights).to(self.device)
            self.model.eval()

            # Set up preprocessor with default normalization
            self.preprocessor = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            logging.info(f"Model '{self.model_name}' loaded successfully")
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

    def classify_image(self, image_data):
        try:
            # Validate image data
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            
            # Preprocess image
            inputs = self.preprocessor(image).unsqueeze(0).to(self.device)

            # Perform inference
            with torch.no_grad():
                outputs = self.model(inputs)
                logits = outputs[0]
                predicted_class_idx = torch.argmax(logits).item()
                confidence_score = F.softmax(logits, dim=0)[predicted_class_idx].item()
                predicted_class = MobileNet_V3_Large_Weights.IMAGENET1K_V2.meta["categories"][predicted_class_idx]

            return predicted_class, confidence_score
        except Exception as e:
            logging.error(f"Error during classification: {e}")
            raise

    def save_file(self, path, data):
        try:
            with open(path, "wb") as f:
                f.write(data)
            logging.info(f"File saved: {path}")
        except Exception as e:
            logging.error(f"Error saving file {path}: {e}")
            raise

    def classify_images(self, ch, method, properties, body, content_id):
        try:
            # Decode BSON message
            obj = decode(body)
            message_content_id = obj["content_id"]
            file_name = obj["file_name"]
            image_data = obj["Payload"]
            PictureID = obj["PictureID"]

            # Ensure the content ID matches
            if message_content_id != content_id:
                logging.info(
                    f"Skipping image with non-matching Content ID: {message_content_id}"
                )
                return

            # Create or use a folder to store images
            target_folder = os.path.abspath(f"store_{content_id}")
            os.makedirs(target_folder, exist_ok=True)

            # Classify the image
            predicted_class, confidence_score = self.classify_image(image_data)

            # Save the image
            image_file_name = f"{file_name}_{message_content_id}.png"
            self.save_file(os.path.join(target_folder, image_file_name), image_data)

            # Log classification result
            logging.info(f"Image classified: {predicted_class}, Confidence: {confidence_score:.2f}")
            predictedString = (f"{predicted_class}, Confidence: {confidence_score:.2f}")

            # Prepare node for database insertion
            image_node = [
                file_name,
                "learnerObject",
                "Image",
                target_folder,
                PictureID,
                predictedString,
            ]

            # Send data to the database
            nodeBuilder.imagePackageParser([image_node], content_id)

            

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except KeyError as e:
            logging.error(f"Missing key in message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logging.error(f"Error processing image message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def consume_image(self, contentID):
        logging.info(f"Starting to consume messages from the Image queue with Content ID: {contentID}")
        
        seen_tags = set()  # To track delivery tags of seen messages

        while True:
            # Fetch a single message from the queue
            method_frame, properties, body = self.channel.basic_get(queue=self.queues["image"], auto_ack=False)

            # If no more messages are in the queue, stop consuming
            if not method_frame:
                logging.info("No more messages in the queue. Stopping consumption.")
                break

            # Detect repetition by checking the delivery tag
            if method_frame.delivery_tag in seen_tags:
                logging.info("Repeated message detected. Stopping consumption.")
                break
            seen_tags.add(method_frame.delivery_tag)

            # Process the message using the classify_images method
            try:
                self.classify_images(self.channel, method_frame, properties, body, contentID)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                # Optionally nack here to requeue the message for later processing
                self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                continue

        # Clean up resources after consumption is complete
        self.cleanup()



    def cleanup(self):
        try:
            if hasattr(self, "channel") and self.channel.is_open:
                self.channel.close()
            if hasattr(self, "connection") and self.connection.is_open:
                self.connection.close()
            logging.info("RabbitMQ connection closed")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def run(self):
        try:
            content_id = input("Enter content ID to process: ").strip()
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


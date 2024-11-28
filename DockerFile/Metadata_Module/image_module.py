import os
import io
import torch
import torch.nn.functional as F
from PIL import Image
import pika
from bson import BSON, decode_all
from transformers import AutoModelForImageClassification, AutoImageProcessor

# Load the pre-trained model and preprocessor
model_name = "microsoft/resnet-50"
model = AutoModelForImageClassification.from_pretrained(model_name)
preprocessor = AutoImageProcessor.from_pretrained(model_name)

FilePath = os.path.dirname(__file__)


def classify_image(image_data, file_name):
    # Open image from bytes
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    inputs = preprocessor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    # Get predicted class index and confidence score
    logits = outputs.logits
    predicted_class_indices = torch.argmax(logits, dim=-1).tolist()
    predicted_class = model.config.id2label[predicted_class_indices[0]]

    # Calculate probabilities using softmax and confidence score
    probabilities = F.softmax(logits, dim=-1)
    confidence_score = probabilities[0, predicted_class_indices].item()

    # Print and return classification results
    print(f"Predicted class: {predicted_class}")
    print(f"Confidence score: {confidence_score:.2f}")
    return predicted_class, confidence_score


def publish_to_rabbitmq(routing_key, message):
    connection_parameters = pika.ConnectionParameters("localhost")
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()
    channel.queue_declare(queue=routing_key, durable=True)

    # Convert to dict and encode once
    if not isinstance(message, dict):
        message = dict(message)

    encoded_message = BSON.encode(message)
    channel.basic_publish(exchange="", routing_key=routing_key, body=encoded_message)
    connection.close()


def on_message_received(ch, method, properties, body):
    try:
        body = decode_all(body)[0]
        image_data = body["Payload"]
        file_name = body["FileName"]
        predicted_class, confidence_score = classify_image(image_data, file_name)

        response_message = {
            "ID": body["ID"],
            "FileName": file_name,
            "Status": "Classification Successful",
            "PredictedClass": predicted_class,
            "ConfidenceScore": float(confidence_score),  # Ensure float type
        }
        publish_to_rabbitmq(".Status.", response_message)
    except Exception as e:
        error_message = {"Status": "Classification Failed", "Message": str(e)}
        publish_to_rabbitmq(".Status.", error_message)
    try:
        body = decode_all(body)[0]  # Decode BSON bytes to dict
        image_data = body["Payload"]
        file_name = body["FileName"]
        predicted_class, confidence_score = classify_image(image_data, file_name)

        response_message = {
            "ID": body["ID"],
            "FileName": file_name,
            "Status": "Classification Successful",
            "PredictedClass": predicted_class,
            "ConfidenceScore": confidence_score,
        }
        publish_to_rabbitmq(".Status.", response_message)
    except Exception as e:
        error_message = {"Status": "Classification Failed", "Message": str(e)}
        publish_to_rabbitmq(".Status.", error_message)


def consumer_connection(routing_key):
    connection_parameters = pika.ConnectionParameters("localhost")
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()

    # Ensure queue exists
    channel.queue_declare(queue=routing_key, durable=True)

    channel.basic_consume(
        queue=routing_key, auto_ack=True, on_message_callback=on_message_received
    )
    print("Image Classification Module Starting Consuming")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.close()
        connection.close()


if __name__ == "__main__":
    consumer_connection("Image")

#Integration Plan 
#DOES NOT PROCESS standalone images - Because it is generic classification 
#only processes images from Document - stores the image  as a learner object and attaches to learner object where it came from and stores predicted
#class and confidence score.  
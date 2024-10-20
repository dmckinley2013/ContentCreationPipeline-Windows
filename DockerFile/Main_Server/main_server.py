import socket
from pymongo import MongoClient
from bson import BSON, ObjectId
import hashlib
import datetime
import random
import logging
import pika
import time

MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 15 MB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compute_unique_id(data_object):
    # Convert the object to a string
    data_str = str(BSON.encode(data_object))
    
    # Append the current date and time
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    combined_data = data_str + current_time + str(random.random())
    
    # Generate SHA-256 hash
    unique_id = hashlib.sha256(combined_data.encode()).hexdigest()
    
    return unique_id

def split_payload(payload):
    return [payload[i:i+MAX_MESSAGE_SIZE] for i in range(0, len(payload), MAX_MESSAGE_SIZE)]

def send_bson_obj(job):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Dashboard', durable=True)

        for key in ['Documents', 'Images', 'Audio']:
            if key in job and len(job[key]) > 0:
                for item in job[key]:
                    try:
                        # Log the type and ID of each item before sending
                        logging.info(f"Sending {key}: ID={item.get('ID')}, FileName={item.get('FileName')}")
                        
                        # Publish the message
                        channel.basic_publish(
                            exchange='',
                            routing_key='Dashboard',
                            body=BSON.encode(item),
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                    except Exception as e:
                        logging.error(f"Failed to send {key} message: {e}")

        logging.info("All messages processed and sent to RabbitMQ")
        connection.close()
    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")



def id_generator(job):
    job['ID'] = compute_unique_id(job)  # Assigning unique ID as a string
    if 'NumberOfDocuments' in job and job['NumberOfDocuments'] > 0:
        for document in job['Documents']:
            document['ID'] = job['ID']
            document['DocumentId'] = compute_unique_id(document)
    if 'NumberOfImages' in job and job['NumberOfImages'] > 0:
        for image in job['Images']:
            image['ID'] = job['ID']
            image['PictureID'] = compute_unique_id(image)
    if 'NumberOfAudio' in job and job['NumberOfAudio'] > 0:
        for audio in job['Audio']:
            audio['ID'] = job['ID']
            audio['AudioID'] = compute_unique_id(audio)
    return job

if __name__ == '__main__':
    job = { 
    "ID": "ObjectID",  
    "NumberOfDocuments": 1,
    "NumberOfImages": 2,
    "NumberOfAudio": 2,
    "Documents": [
        {
            "ID": "ObjectID",  
            "DocumentId": "ObjectID",
            "DocumentType": "String",
            "FileName": "String",
            "Payload": b"Binary"
        }
    ],
    "Images": [
        {
            "ID": "ObjectID", 
            "PictureID": "ObjectID",
            "PictureType": "String",
            "FileName": "String",
            "Payload": b"Binary"
        }
    ],
    "Audio": [
        {
            "ID": "ObjectID", 
            "AudioID": "ObjectID",
            "AudioType": "String",
            "FileName": "String",
            "Payload": b"Binary"
        },
        {
            "ID": "ObjectID", 
            "AudioID": "ObjectID",
            "AudioType": "String",
            "FileName": "String",
            "Payload": b"Binary2"
        }
    ],
    
}
    # take binary data from file
    try:
        with open('Project_4.pdf', 'rb') as f:
            job['Documents'][0]['Payload'] = f.read()
            job['Documents'][0]["DocumentType"] = "pdf"
            job['Documents'][0]["FileName"] = f.name
        with open('x.png', 'rb') as f:
            job['Images'][0]['Payload'] = f.read()
            job['Images'][0]["PictureType"] = "png"
            job['Images'][0]["FileName"] = f.name
        with open('audio.mp3', 'rb') as f:
            job['Audio'][0]['Payload'] = f.read()
            job['Audio'][0]["AudioType"] = "mp3"
            job['Audio'][0]["FileName"] = f.name
        with open('audio2.mp3', 'rb') as f:
            job['Audio'][1]['Payload'] = f.read()
            job['Audio'][1]["AudioType"] = "mp3"
            job['Audio'][1]["FileName"] = f.name
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        exit(1)

    id_generator(job)

    logging.info(f"Documents: {len(job['Documents'])}")
    logging.info(f"Images: {len(job['Images'])}")
    logging.info(f"Audio: {len(job['Audio'])}")

    send_bson_obj(job)
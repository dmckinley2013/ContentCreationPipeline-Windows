import socket
from pymongo import MongoClient
from bson import BSON, ObjectId
import hashlib
import datetime
import random
import logging
import pika

MAX_MESSAGE_SIZE = 15 * 1024 * 1024  # 15 MB

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
        
        # Split large payloads
        for key in ['Documents', 'Images', 'Audio', 'Video']:
            if key in job and len(job[key]) > 0:
                for item in job[key]:
                    if 'Payload' in item and len(item['Payload']) > MAX_MESSAGE_SIZE:
                        chunks = split_payload(item['Payload'])
                        for i, chunk in enumerate(chunks):
                            chunk_message = item.copy()
                            chunk_message['Payload'] = chunk
                            chunk_message['ChunkNumber'] = i + 1
                            chunk_message['TotalChunks'] = len(chunks)
                            
                            channel.basic_publish(
                                exchange='',
                                routing_key='Dashboard',
                                body=BSON.encode(chunk_message),
                                properties=pika.BasicProperties(delivery_mode=2)
                            )
                    else:
                        channel.basic_publish(
                            exchange='',
                            routing_key='Dashboard',
                            body=BSON.encode(item),
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
        
        logging.info("Messages sent to RabbitMQ")
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
    if 'NumberOfVideo' in job and job['NumberOfVideo'] > 0:
        for video in job['Video']:
            video['ID'] = job['ID']
            video['VideoID'] = compute_unique_id(video)
    return job

if __name__ == '__main__':
    job = { 
    "ID": "ObjectID",  
    "NumberOfDocuments": 1,
    "NumberOfImages": 2,
    "NumberOfAudio": 2,
    "NumberOfVideo": 1,
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
    "Video": [
        {
            "ID": "ObjectID", 
            "VideoID": "ObjectID",
            "VideoType": "String",
            "FileName": "String",
            "Payload": b"Binary5"
        },
    ],
}
    # take binary data from file
    try:
        with open('Project_4.pdf', 'rb') as f:
            job['Documents'][0]['Payload'] = f.read()
            job['Documents'][0]["DocumentType"] = "pdf"
            job['Documents'][0]["FileName"] = f.name
        with open('my_video.mp4', 'rb') as f:
            job['Video'][0]['Payload'] = f.read()
            job['Video'][0]["VideoType"] = "mp4"
            job['Video'][0]["FileName"] = f.name
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
    logging.info(f"Video: {len(job['Video'])}")

    send_bson_obj(job)
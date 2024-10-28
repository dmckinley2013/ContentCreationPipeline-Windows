import socket
from pymongo import MongoClient
from bson import BSON, ObjectId
import hashlib
import datetime
import random
import logging
import pika
import time

MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100 MB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compute_unique_id(data_object):
    data_str = str(BSON.encode(data_object))
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    combined_data = data_str + current_time + str(random.random())
    unique_id = hashlib.sha256(combined_data.encode()).hexdigest()
    return unique_id

def split_payload(payload):
    return [payload[i:i+MAX_MESSAGE_SIZE] for i in range(0, len(payload), MAX_MESSAGE_SIZE)]

def send_bson_obj(job):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Dashboard', durable=True)

        def get_content_type(key, item):
            if key == 'Documents':
                return 'Document'
            elif key == 'Images':
                return 'Image'
            elif key == 'Audio':
                return 'Audio'
            return 'Unknown'

        for key in ['Documents', 'Images', 'Audio']:
            if key in job and len(job[key]) > 0:
                for item in job[key]:
                    try:
                        message_data = {
                            'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                            'job_id': item['ID'],
                            'content_id': item.get('DocumentId') or item.get('PictureID') or item.get('AudioID'),
                            'content_type': get_content_type(key, item),
                            'file_name': item['FileName'],
                            'status': 'Processed',
                            'message': f"{get_content_type(key, item)} file '{item['FileName']}' successfully sent to {key} queue"
                        }

                        channel.basic_publish(
                            exchange='',
                            routing_key='Dashboard',
                            body=BSON.encode(message_data),
                            properties=pika.BasicProperties(delivery_mode=2)
                        )

                        logging.info(f"Successfully sent {key}: ID={item.get('ID')}, FileName={item.get('FileName')}")
                    except Exception as e:
                        logging.error(f"Failed to send {key}: {e}")

        logging.info("All messages processed and sent to RabbitMQ")
        connection.close()

    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")

def id_generator(job):
    job['ID'] = compute_unique_id(job)
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
    num_messages = 4  # You can change this to any number you want
    split_jobs = True  # Set to True for multiple jobs, False for one job

    base_job = { 
        "ID": "ObjectID",  
        "NumberOfDocuments": 2,
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

    try:
        with open('Project_4.pdf', 'rb') as f:
            base_job['Documents'][0]['Payload'] = f.read()
            base_job['Documents'][0]["DocumentType"] = "pdf"
            base_job['Documents'][0]["FileName"] = f.name
        with open('x.png', 'rb') as f:
            base_job['Images'][0]['Payload'] = f.read()
            base_job['Images'][0]["PictureType"] = "png"
            base_job['Images'][0]["FileName"] = f.name
        with open('audio.mp3', 'rb') as f:
            base_job['Audio'][0]['Payload'] = f.read()
            base_job['Audio'][0]["AudioType"] = "mp3"
            base_job['Audio'][0]["FileName"] = f.name
        with open('audio2.mp3', 'rb') as f:
            base_job['Audio'][1]['Payload'] = f.read()
            base_job['Audio'][1]["AudioType"] = "mp3"
            base_job['Audio'][1]["FileName"] = f.name
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        exit(1)

    if split_jobs:
        for i in range(num_messages):
            job = base_job.copy()
            job = id_generator(job)  # Generate unique IDs for job and content

            logging.info(f"Sending job {i+1}/{num_messages} - Job ID: {job['ID']}")
            send_bson_obj(job)
            time.sleep(0.1)  # Optional delay between messages
    else:
        full_job = base_job.copy()
        full_job['NumberOfDocuments'] = num_messages
        full_job['Documents'] = [base_job['Documents'][0].copy() for _ in range(num_messages)]
        full_job['NumberOfImages'] = num_messages * 2
        full_job['Images'] = [base_job['Images'][0].copy() for _ in range(num_messages * 2)]
        full_job['NumberOfAudio'] = num_messages * 2
        full_job['Audio'] = [base_job['Audio'][0].copy() for _ in range(num_messages * 2)]

        full_job = id_generator(full_job)  # Generate unique IDs for the full job
        logging.info(f"Sending one large job with {num_messages} content items - Job ID: {full_job['ID']}")
        send_bson_obj(full_job)

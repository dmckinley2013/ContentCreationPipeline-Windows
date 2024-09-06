import socket
from bson import BSON
from bson import decode_all
import hashlib
import datetime
import json
import random
import os

def compute_unique_id(data_object):
    # Convert the object to a JSON string first
    data_str = json.dumps(data_object, sort_keys=True, default=str)
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    combined_data = data_str + current_time + str(random.random())
    return hashlib.sha256(combined_data.encode()).hexdigest()

def send_bson_obj(job):   
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 12345))
        bson_data = BSON.encode(job)
        s.sendall(bson_data)
        print("Data sent successfully")
    except Exception as e:
        print(f"Error sending data: {e}")
    finally:
        s.close()

def id_generator(job):
    job['ID'] = compute_unique_id(job)
    for category in ['Documents', 'Images', 'Audio', 'Video']:
        if f'NumberOf{category}' in job and job[f'NumberOf{category}'] > 0:
            for item in job[category]:
                item['ID'] = job['ID']
                item[f'{category[:-1]}ID' if category != 'Documents' else 'DocumentId'] = compute_unique_id(item)
    return job

def read_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return f.read(), os.path.basename(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None, None

if __name__ == '__main__':
    job = { 
        "ID": "ObjectID",  
        "NumberOfDocuments": 2,  # Adjusted for 2 documents
        "NumberOfImages": 1,
        "NumberOfAudio": 2,
        "NumberOfVideo": 1,
        "Documents": [
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Payload": b"Binary"
            },
            
            {
                "ID": "ObjectID",
                "DocumentId": "ObjectID",
                "DocumentType": "txt",  
                "FileName": "hello_world.txt",
                "Payload": b"Hello, World!"  
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

    script_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_read = [
        ('Project_4.pdf', 'Documents', 0, 'DocumentType', 'pdf'),
        ('my_video.mp4', 'Video', 0, 'VideoType', 'mp4'),
        ('x.png', 'Images', 0, 'PictureType', 'png'),
        ('audio.mp3', 'Audio', 0, 'AudioType', 'mp3'),
        ('audio2.mp3', 'Audio', 1, 'AudioType', 'mp3')
    ]

    for filename, category, index, type_key, file_type in files_to_read:
        file_path = os.path.join(script_dir, filename)
        payload, name = read_file(file_path)
        if payload is not None:
            job[category][index]['Payload'] = payload
            job[category][index][type_key] = file_type
            job[category][index]["FileName"] = name
        else:
            print(f"Warning: Failed to load {filename}. The {category} data may be incomplete.")

    id_generator(job)
    send_bson_obj(job)
    print("Script execution completed.")

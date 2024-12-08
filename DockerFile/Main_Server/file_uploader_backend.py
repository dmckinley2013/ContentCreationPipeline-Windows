from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import hashlib
import datetime
import random
from bson import encode
import socket
import asyncio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def compute_unique_id(data_object):
    data_str = str(encode(data_object))
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    combined_data = data_str + current_time + str(random.random())
    return hashlib.sha256(combined_data.encode()).hexdigest()


async def send_bson_obj(job):
    try:
        reader, writer = await asyncio.open_connection("localhost", 12349)
        writer.write(encode(job))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_files(
    document: UploadFile = File(None),
    image: UploadFile = File(None),
    audio: List[UploadFile] = File(None),
    video: UploadFile = File(None),
):
    job = {
        "ID": "ObjectID",
        "NumberOfDocuments": 0,
        "NumberOfImages": 0,
        "NumberOfAudio": 0,
        "NumberOfVideo": 0,
        "Documents": [],
        "Images": [],
        "Audio": [],
        "Video": [],
    }

    # Process document
    if document:
        content = await document.read()
        job["Documents"].append(
            {
                "ID": "ObjectID",
                "content_id": "ObjectID",
                "DocumentType": document.filename.split(".")[-1],
                "file_name": document.filename,
                "Payload": content,
            }
        )
        job["NumberOfDocuments"] = 1

    # Process image
    if image:
        content = await image.read()
        job["Images"].append(
            {
                "ID": "ObjectID",
                "content_id": "ObjectID",
                "PictureType": image.filename.split(".")[-1],
                "file_name": image.filename,
                "Payload": content,
            }
        )
        job["NumberOfImages"] = 1

    # Process audio files
    if audio:
        for audio_file in audio:
            content = await audio_file.read()
            job["Audio"].append(
                {
                    "ID": "ObjectID",
                    "content_id": "ObjectID",
                    "AudioType": audio_file.filename.split(".")[-1],
                    "file_name": audio_file.filename,
                    "Payload": content,
                }
            )
        job["NumberOfAudio"] = len(job["Audio"])

    # Process video
    if video:
        content = await video.read()
        job["Video"].append(
            {
                "ID": "ObjectID",
                "VideoID": "ObjectID",
                "VideoType": video.filename.split(".")[-1],
                "file_name": video.filename,
                "Payload": content,
            }
        )
        job["NumberOfVideo"] = 1

    # Generate IDs
    job["ID"] = compute_unique_id(job)

    if job["NumberOfDocuments"] > 0:
        for document in job["Documents"]:
            document["ID"] = job["ID"]
            document["content_id"] = compute_unique_id(document)
            document["DocumentId"] = compute_unique_id(document)
            
    if job["NumberOfImages"] > 0:
        for image in job["Images"]:
            image["ID"] = job["ID"]
            image["content_id"] = compute_unique_id(image)
            image['PictureID'] = compute_unique_id(image)
    if job["NumberOfAudio"] > 0:
        for audio in job["Audio"]:
            audio["ID"] = job["ID"]
            audio["content_id"] = compute_unique_id(audio)
            audio["AudioID"] = compute_unique_id(audio)
    if job["NumberOfVideo"] > 0:
        for video in job["Video"]:
            video["ID"] = job["ID"]
            video["content_id"] = compute_unique_id(video)
            video["VideoID"] = compute_unique_id(video)

    # Send to existing socket service
    await send_bson_obj(job)

    return {"message": "Files uploaded successfully", "job_id": job["ID"]}

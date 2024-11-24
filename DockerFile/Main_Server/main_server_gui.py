import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from bson import BSON
import hashlib
import datetime
import json
import random
from pathlib import Path
import pika
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FileUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Uploader")
        self.root.geometry("600x800")

        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize job dictionary with empty lists
        self.job = {
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

        # Queue configuration
        self.queues = {
            'Documents': 'Document',
            'Images': 'Image',
            'Audio': 'Audio',
            'Video': 'Video',
            'Dashboard': 'Dashboard'
        }

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure main frame grid
        for i in range(5):
            main_frame.grid_columnconfigure(i, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="File Uploader", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=5, pady=(0, 20))

        # Document Section
        section_frame = ttk.LabelFrame(main_frame, text="Document", padding="10")
        section_frame.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 15), padx=5)

        self.doc_label = ttk.Label(section_frame, text="No file selected")
        self.doc_label.grid(row=0, column=0, columnspan=5, pady=5)

        ttk.Button(section_frame, text="Select Document", command=lambda: self.select_file("document")).grid(row=1, column=1, padx=5)
        ttk.Button(section_frame, text="Clear", command=lambda: self.clear_file("document")).grid(row=1, column=3, padx=5)

        # Image Section
        section_frame = ttk.LabelFrame(main_frame, text="Image", padding="10")
        section_frame.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(0, 15), padx=5)

        self.img_label = ttk.Label(section_frame, text="No file selected")
        self.img_label.grid(row=0, column=0, columnspan=5, pady=5)

        ttk.Button(section_frame, text="Select Image", command=lambda: self.select_file("image")).grid(row=1, column=1, padx=5)
        ttk.Button(section_frame, text="Clear", command=lambda: self.clear_file("image")).grid(row=1, column=3, padx=5)

        # Audio Section
        section_frame = ttk.LabelFrame(main_frame, text="Audio Files", padding="10")
        section_frame.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(0, 15), padx=5)

        self.audio_frame = ttk.Frame(section_frame)
        self.audio_frame.grid(row=0, column=0, columnspan=5, pady=5)
        ttk.Label(self.audio_frame, text="No audio files selected").grid(row=0, column=0)

        ttk.Button(section_frame, text="Add Audio", command=lambda: self.select_file("audio")).grid(row=1, column=1, padx=5)
        ttk.Button(section_frame, text="Clear All", command=lambda: self.clear_file("audio")).grid(row=1, column=3, padx=5)

        # Video Section
        section_frame = ttk.LabelFrame(main_frame, text="Video", padding="10")
        section_frame.grid(row=4, column=0, columnspan=5, sticky="ew", pady=(0, 15), padx=5)

        self.video_label = ttk.Label(section_frame, text="No file selected")
        self.video_label.grid(row=0, column=0, columnspan=5, pady=5)

        ttk.Button(section_frame, text="Select Video", command=lambda: self.select_file("video")).grid(row=1, column=1, padx=5)
        ttk.Button(section_frame, text="Clear", command=lambda: self.clear_file("video")).grid(row=1, column=3, padx=5)

        # Upload Button
        style = ttk.Style()
        style.configure("Upload.TButton", font=("Arial", 11))
        upload_btn = ttk.Button(main_frame, text="Upload Files", command=self.upload_files, style="Upload.TButton")
        upload_btn.grid(row=5, column=1, columnspan=3, pady=20, sticky="ew")

        # Status Label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=6, column=0, columnspan=5, pady=5)

    def update_audio_list(self):
        for widget in self.audio_frame.winfo_children():
            widget.destroy()

        if not self.job["Audio"]:
            ttk.Label(self.audio_frame, text="No audio files selected").grid(row=0, column=0)
            return

        for i, audio in enumerate(self.job["Audio"]):
            frame = ttk.Frame(self.audio_frame)
            frame.grid(row=i, column=0, sticky="ew", pady=2)

            filename = audio["FileName"]
            if len(filename) > 40:
                filename = filename[:37] + "..."

            ttk.Label(frame, text=f"{i+1}. {filename}").grid(row=0, column=0, padx=(0, 10))
            ttk.Button(frame, text="Remove", command=lambda idx=i: self.remove_audio(idx)).grid(row=0, column=1)

    def remove_audio(self, index):
        self.job["Audio"].pop(index)
        self.job["NumberOfAudio"] = len(self.job["Audio"])
        self.update_audio_list()

    def clear_file(self, file_type):
        if file_type == "document":
            self.job["Documents"] = []
            self.job["NumberOfDocuments"] = 0
            self.doc_label.config(text="No file selected")
        elif file_type == "image":
            self.job["Images"] = []
            self.job["NumberOfImages"] = 0
            self.img_label.config(text="No file selected")
        elif file_type == "audio":
            self.job["Audio"] = []
            self.job["NumberOfAudio"] = 0
            self.update_audio_list()
        elif file_type == "video":
            self.job["Video"] = []
            self.job["NumberOfVideo"] = 0
            self.video_label.config(text="No file selected")

    def select_file(self, file_type):
        filetypes = {
            "document": [("PDF files", "*.pdf"), ("All files", "*.*")],
            "image": [("Image files", "*.png;*.jpg;*.jpeg;*.gif"), ("All files", "*.*")],
            "audio": [("Audio files", "*.mp3;*.wav"), ("All files", "*.*")],
            "video": [("Video files", "*.mp4;*.avi;*.mov"), ("All files", "*.*")],
        }

        filename = filedialog.askopenfilename(filetypes=filetypes[file_type])
        if filename:
            if file_type == "document":
                self.doc_label.config(text=Path(filename).name)
                with open(filename, "rb") as f:
                    self.job["Documents"] = [{
                        "ID": "ObjectID",
                        "DocumentId": "ObjectID",
                        "DocumentType": Path(filename).suffix[1:],
                        "FileName": Path(filename).name,
                        "Payload": f.read(),
                    }]
                    self.job["NumberOfDocuments"] = 1
            elif file_type == "image":
                self.img_label.config(text=Path(filename).name)
                with open(filename, "rb") as f:
                    self.job["Images"] = [{
                        "ID": "ObjectID",
                        "PictureID": "ObjectID",
                        "PictureType": Path(filename).suffix[1:],
                        "FileName": Path(filename).name,
                        "Payload": f.read(),
                    }]
                    self.job["NumberOfImages"] = 1
            elif file_type == "audio":
                with open(filename, "rb") as f:
                    self.job["Audio"].append({
                        "ID": "ObjectID",
                        "AudioID": "ObjectID",
                        "AudioType": Path(filename).suffix[1:],
                        "FileName": Path(filename).name,
                        "Payload": f.read(),
                    })
                    self.job["NumberOfAudio"] = len(self.job["Audio"])
                self.update_audio_list()
            elif file_type == "video":
                self.video_label.config(text=Path(filename).name)
                with open(filename, "rb") as f:
                    self.job["Video"] = [{
                        "ID": "ObjectID",
                        "VideoID": "ObjectID",
                        "VideoType": Path(filename).suffix[1:],
                        "FileName": Path(filename).name,
                        "Payload": f.read(),
                    }]
                    self.job["NumberOfVideo"] = 1

    def compute_unique_id(self, data_object):
        data_str = str(BSON.encode(data_object))
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        combined_data = data_str + current_time + str(random.random())
        return hashlib.sha256(combined_data.encode()).hexdigest()

    def id_generator(self, job):
        job["ID"] = self.compute_unique_id(job)
        if job["NumberOfDocuments"] > 0:
            for document in job["Documents"]:
                document["ID"] = job["ID"]
                document["DocumentId"] = self.compute_unique_id(document)
        if job["NumberOfImages"] > 0:
            for image in job["Images"]:
                image["ID"] = job["ID"]
                image["PictureID"] = self.compute_unique_id(image)
        if job["NumberOfAudio"] > 0:
            for audio in job["Audio"]:
                audio["ID"] = job["ID"]
                audio["AudioID"] = self.compute_unique_id(audio)
        if job["NumberOfVideo"] > 0:
            for video in job["Video"]:
                video["ID"] = job["ID"]
                video["VideoID"] = self.compute_unique_id(video)
        return job

    def send_bson_obj(self, job):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()

            # Declare queues passively (don't create or modify if they exist)
            for queue_name in self.queues.values():
                try:
                    channel.queue_declare(queue=queue_name, passive=True)
                except pika.exceptions.ChannelClosedByBroker:
                    # Reconnect if channel was closed
                    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
                    channel = connection.channel()
                    # Create queue if it doesn't exist
                    channel.queue_declare(queue=queue_name, durable=True)

            def get_content_type(key, item):
                if key == 'Documents':
                    return 'Document'
                elif key == 'Images':
                    return 'Image'
                elif key == 'Audio':
                    return 'Audio'
                elif key == 'Video':
                    return 'Video'
                return 'Unknown'

            for key in ['Documents', 'Images', 'Audio', 'Video']:
                if key in job and len(job[key]) > 0:
                    for item in job[key]:
                        try:
                            # Prepare dashboard message
                            dashboard_message = {
                                'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                                'job_id': item['ID'],
                                'content_id': item.get('DocumentId') or item.get('PictureID') or item.get('AudioID') or item.get('VideoID'),
                                'content_type': get_content_type(key, item),
                                'file_name': item['FileName'],
                                'status': 'Processed',
                                'message': f"{get_content_type(key, item)} file '{item['FileName']}' successfully sent to {key} queue"
                            }

                            # Send to dashboard queue
                            channel.basic_publish(
                                exchange='',
                                routing_key='Dashboard',
                                body=BSON.encode(dashboard_message),
                                properties=pika.BasicProperties(delivery_mode=2)
                            )

                            # Send to content-specific queue
                            channel.basic_publish(
                                exchange='',
                                routing_key=self.queues[key],
                                body=BSON.encode(item),
                                properties=pika.BasicProperties(delivery_mode=2)
                            )

                            logging.info(f"Successfully sent {key}: ID={item.get('ID')}, FileName={item.get('FileName')} to {self.queues[key]}")
                        except Exception as e:
                            logging.error(f"Failed to send {key}: {e}")
                            raise

            connection.close()
            return True

        except Exception as e:
            logging.error(f"Failed to send message to RabbitMQ: {e}")
            return str(e)

    def upload_files(self):
        # Check if at least one file is selected
        if (
            self.job["NumberOfDocuments"]
            + self.job["NumberOfImages"]
            + self.job["NumberOfAudio"]
            + self.job["NumberOfVideo"]
        ) == 0:
            messagebox.showwarning("Warning", "Please select at least one file to upload")
            return

        # Generate IDs and send data
        self.status_label.config(text="Processing...")
        self.root.update()

        try:
            processed_job = self.id_generator(self.job)
            result = self.send_bson_obj(processed_job)

            if result is True:
                self.status_label.config(text="Files uploaded successfully!")
                messagebox.showinfo("Success", "Files have been uploaded successfully!")
                # Clear all files after successful upload
                self.clear_file("Document")
                self.clear_file("Image")
                self.clear_file("Audio")
                self.clear_file("Video")
            else:
                self.status_label.config(text=f"Upload failed: {result}")
                messagebox.showerror("Error", f"Upload failed: {result}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")


def main():
    root = tk.Tk()
    app = FileUploaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
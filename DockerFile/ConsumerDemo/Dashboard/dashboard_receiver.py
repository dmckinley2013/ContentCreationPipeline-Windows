import tkinter as tk
from tkinter import ttk, messagebox
from pymongo import MongoClient
import pika
from bson import BSON
from threading import Thread
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Message Dashboard")
        self.geometry("1200x600")
        self.chunk_buffer = {}
        self.columns = ("Time", "JobID", "ContentID", "ContentType", "FileName", "Status", "Message")

        self.setup_ui()
        self.init_db()
        self.load_messages()
        self.start_consuming_thread()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title_label = ttk.Label(self, text="Message Dashboard", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        clear_button = ttk.Button(self, text="Clear All Messages", command=self.clear_all_messages)
        clear_button.grid(row=1, column=0, padx=10, pady=5, sticky="e")

        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_column(_col, False))
            self.tree.column(col, width=170, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.bind("<Double-1>", self.on_item_click)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=3, column=0, sticky="ew")
        self.update_status("Ready")

    def update_status(self, message):
        self.status_var.set(message)

    def init_db(self):
        try:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['dashboard_db']
            self.collection = self.db['messages']
            logging.info("Connected to MongoDB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            messagebox.showerror("Database Error", f"Failed to connect to MongoDB: {e}")
            self.quit()

    def start_consuming_thread(self):
        thread = Thread(target=self.consume_messages)
        thread.daemon = True
        thread.start()

    def consume_messages(self):
        try:
            connection_parameters = pika.ConnectionParameters('localhost')
            connection = pika.BlockingConnection(connection_parameters)
            channel = connection.channel()
            
            queue_name = 'Dashboard'
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_consume(queue=queue_name, on_message_callback=self.on_message_received, auto_ack=True)
            
            logging.info('Starting Consuming')
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Error consuming messages: {e}")

    def on_message_received(self, ch, method, properties, body):
        try:
            decoded_body = BSON(body).decode()
            logging.info(f"Received new message: {decoded_body}")
            
            if 'ChunkNumber' in decoded_body:
                self.handle_chunked_message(decoded_body)
            else:
                self.save_message_to_db(decoded_body)
                self.display_message(decoded_body)
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def handle_chunked_message(self, chunk):
        key = (chunk['ID'], chunk.get('DocumentId') or chunk.get('PictureID') or chunk.get('AudioID') or chunk.get('VideoID'))
        if key not in self.chunk_buffer:
            self.chunk_buffer[key] = {}
        
        self.chunk_buffer[key][chunk['ChunkNumber']] = chunk
        
        if len(self.chunk_buffer[key]) == chunk['TotalChunks']:
            full_message = self.reassemble_chunks(self.chunk_buffer[key])
            self.save_message_to_db(full_message)
            self.display_message(full_message)
            del self.chunk_buffer[key]

    def reassemble_chunks(self, chunks):
        sorted_chunks = sorted(chunks.items())
        reassembled = sorted_chunks[0][1].copy()
        reassembled['Payload'] = b''.join(chunk['Payload'] for _, chunk in sorted_chunks)
        del reassembled['ChunkNumber']
        del reassembled['TotalChunks']
        return reassembled

    def save_message_to_db(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        job_id = message.get('ID', 'Unknown JobID')
        content_id, content_type = self.get_content_info(message)
        file_name = message.get('FileName', 'Unknown File')
        status = message.get('Status', 'Processed')
        message_text = message.get('Message', 'No additional information')

        if status.lower() == 'processed':
            status = 'Successfully Processed'
            if message_text == 'No additional information':
                message_text = 'Message successfully processed and sent'
        else:
            status = 'Processing Failed'
            if message_text == 'No additional information':
                message_text = 'Message processing or sending failed'

        document = {
            "time": timestamp,
            "job_id": job_id,
            "content_id": content_id,
            "content_type": content_type,
            "file_name": file_name,
            "status": status,
            "message": message_text
        }

        try:
            self.collection.insert_one(document)
            logging.info(f"Saved message to MongoDB: {job_id}")
        except Exception as e:
            logging.error(f"Failed to save message to MongoDB: {e}")

    def get_content_info(self, message):
        if 'DocumentId' in message:
            return message['DocumentId'], 'Document'
        elif 'PictureID' in message:
            return message['PictureID'], 'Picture'
        elif 'AudioID' in message:
            return message['AudioID'], 'Audio'
        elif 'VideoID' in message:
            return message['VideoID'], 'Video'
        else:
            return 'Unknown ContentID', 'Unknown Type'

    def load_messages(self):
        try:
            messages = self.collection.find().sort("time", -1)
            for message in messages:
                self.insert_message(message)
            self.update_status("Messages loaded from database")
            logging.info("Loaded messages from MongoDB")
        except Exception as e:
            self.update_status("Failed to load messages")
            logging.error(f"Failed to load messages from MongoDB: {e}")

    def insert_message(self, message):
        row = (
            message['time'],
            message['job_id'],
            message['content_id'],
            message['content_type'],
            message['file_name'],
            message['status'],
            message['message']
        )
        self.tree.insert("", tk.END, values=row)

    def display_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        job_id = message.get('ID', 'Unknown JobID')
        content_id, content_type = self.get_content_info(message)
        file_name = message.get('FileName', 'Unknown File')
        status = message.get('Status', 'Processed')
        message_text = message.get('Message', 'No additional information')

        if status.lower() == 'processed':
            status = 'Successfully Processed'
            if message_text == 'No additional information':
                message_text = 'Message successfully processed and sent'
        else:
            status = 'Processing Failed'
            if message_text == 'No additional information':
                message_text = 'Message processing or sending failed'

        row = (timestamp, job_id, content_id, content_type, file_name, status, message_text)
        self.tree.insert("", 0, values=row)
        self.update_status(f"New message received: {job_id}")
        logging.info(f"Displayed message: {job_id}")

    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(key=lambda x: x[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def on_item_click(self, event):
        item = self.tree.selection()[0]
        message = self.tree.item(item, "values")
        
        popup = tk.Toplevel(self)
        popup.title("Message Details")
        popup.geometry("600x400")
        
        text = tk.Text(popup, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        for i, column in enumerate(self.columns):
            text.insert(tk.END, f"{column}: {message[i]}\n\n")
        
        text.config(state=tk.DISABLED)

    def clear_all_messages(self):
        if messagebox.askyesno("Clear All Messages", "Are you sure you want to clear all messages?"):
            self.tree.delete(*self.tree.get_children())
            try:
                self.collection.delete_many({})
                self.update_status("All messages cleared")
                logging.info("All messages cleared from MongoDB")
            except Exception as e:
                self.update_status("Failed to clear messages")
                logging.error(f"Failed to clear messages from MongoDB: {e}")

if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
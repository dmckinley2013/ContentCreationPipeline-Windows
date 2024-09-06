import tkinter as tk
from tkinter import ttk
import sqlite3
import pika
from bson import BSON
from threading import Thread
from datetime import datetime

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Message Dashboard")
        self.geometry("1200x600")

        # Frame for the title
        title_frame = tk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=5)

        title_label = tk.Label(title_frame, text="Message Dashboard", font=('Arial', 16, 'bold'))
        title_label.pack()

        # Treeview widget to display messages
        self.tree = ttk.Treeview(self, columns=("Time", "ID", "DocumentId", "DocumentType", "FileName", "Status", "Message"), show="headings")
        self.tree.heading("Time", text="Time", command=lambda: self.sort_column("Time", False))
        self.tree.heading("ID", text="ID", command=lambda: self.sort_column("ID", False))
        self.tree.heading("DocumentId", text="Document ID", command=lambda: self.sort_column("DocumentId", False))
        self.tree.heading("DocumentType", text="Document Type", command=lambda: self.sort_column("DocumentType", False))
        self.tree.heading("FileName", text="File Name", command=lambda: self.sort_column("FileName", False))
        self.tree.heading("Status", text="Status", command=lambda: self.sort_column("Status", False))
        self.tree.heading("Message", text="Message", command=lambda: self.sort_column("Message", False))
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar for the Treeview
        scrollbar = tk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Initialize the database and load existing messages
        self.init_db()
        self.load_messages()

        # Start the message consumption thread
        self.start_consuming_thread()

        # Bind the double-click event to show a popup with message details
        self.tree.bind("<Double-1>", self.on_item_click)

    def init_db(self):
        # Database setup in the main thread
        self.conn = sqlite3.connect("messages.db")
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                          (id INTEGER PRIMARY KEY, time TEXT, message_id TEXT, 
                           document_id TEXT, document_type TEXT, file_name TEXT, 
                           status TEXT, message TEXT)''')
        self.conn.commit()

    def start_consuming_thread(self):
        thread = Thread(target=self.consume_messages)
        thread.daemon = True
        thread.start()

    def consume_messages(self):
        try:
            # Establish connection to RabbitMQ
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()

            # Connect to the 'Dashboard' queue
            channel.basic_consume(queue='Dashboard', on_message_callback=self.callback, auto_ack=True)
            channel.start_consuming()
        except Exception as e:
            print(f"Error consuming messages: {e}")

    def callback(self, ch, method, properties, body):
        if body:
            try:
                message = BSON.decode(body)
                self.save_message_to_db(message)
                self.display_message(message)
            except Exception as e:
                print(f"Error decoding message: {e}")
                error_message = {"ID": "Unknown", "DocumentType": "Unknown", "FileName": "Unknown",
                                 "Status": "Error", "Message": "Message could not be decoded"}
                self.save_message_to_db(error_message)
                self.display_message(error_message)
        else:
            error_message = {"ID": "Unknown", "DocumentType": "Unknown", "FileName": "Unknown",
                             "Status": "Error", "Message": "Received an empty message"}
            self.save_message_to_db(error_message)
            self.display_message(error_message)

    def save_message_to_db(self, message):
        conn = sqlite3.connect("messages.db")
        cursor = conn.cursor()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_id = message.get('ID', 'Unknown ID')
        document_id = message.get('DocumentId', 
                        message.get('PictureID', 
                        message.get('AudioID', 
                        message.get('VideoID', 'Unknown DocumentId'))))
        document_type = message.get('DocumentType', 
                          message.get('PictureType', 
                          message.get('AudioType', 
                          message.get('VideoType', 'Unknown Type'))))
        file_name = message.get('FileName', 'Unknown File')
        status = message.get('Status', 'Unknown Status')
        message_text = message.get('Message', 'No message')

        cursor.execute('''INSERT INTO messages (time, message_id, document_id, document_type, file_name, status, message)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                          (timestamp, message_id, document_id, document_type, file_name, status, message_text))
        conn.commit()
        conn.close()  # Close the connection to avoid thread issues

    def load_messages(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT time, message_id, document_id, document_type, file_name, status, message FROM messages")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def display_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_id = message.get('ID', 'Unknown ID')
        document_id = message.get('DocumentId', 
                        message.get('PictureID', 
                        message.get('AudioID', 
                        message.get('VideoID', 'Unknown DocumentId'))))
        document_type = message.get('DocumentType', 
                          message.get('PictureType', 
                          message.get('AudioType', 
                          message.get('VideoType', 'Unknown Type'))))
        file_name = message.get('FileName', 'Unknown File')
        status = message.get('Status', 'Unknown Status')
        message_text = message.get('Message', 'No message')

        self.tree.insert("", tk.END, values=(timestamp, message_id, document_id, document_type, file_name, status, message_text))

    def sort_column(self, col, reverse):
        data_list = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        data_list.sort(reverse=reverse)

        for index, (val, child) in enumerate(data_list):
            self.tree.move(child, '', index)

        self.tree.heading(col, command=lambda _col=col: self.sort_column(_col, not reverse))

    def on_item_click(self, event):
        selected_item = self.tree.selection()  # Get selected item
        if selected_item:
            item_data = self.tree.item(selected_item)['values']  # Get the data from the selected item
            # Create a new popup window
            popup = tk.Toplevel(self)
            popup.title("Message Details")
            popup.geometry("400x300")
            
            # Display the details of the clicked message in the popup
            message_details = f"Time: {item_data[0]}\nID: {item_data[1]}\nDocument ID: {item_data[2]}\n"
            message_details += f"Document Type: {item_data[3]}\nFile Name: {item_data[4]}\nStatus: {item_data[5]}\nMessage: {item_data[6]}"
            
            # Label to display message details in the popup
            message_label = tk.Label(popup, text=message_details, anchor="w", justify="left")
            message_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Initialize the app
if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()

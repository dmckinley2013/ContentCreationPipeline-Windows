import socket
from bson import BSON, encode, decode  # Binary JSON format , windows
import threading  # For handling multiple clients concurrently
import pika  # RabbitMQ client library
from pika.exchange_type import ExchangeType
from copy import deepcopy  # Import deepcopy if you need a deep copy
import datetime

def recvall(sock, expected_length):
    data = b''
    while len(data) < expected_length:
        more_data = sock.recv(expected_length - len(data))
        if not more_data:
            raise Exception("Socket closed before we received the complete document")
        data += more_data
    return data

def handle_client(client):
    # Initially, receive the length of the BSON document (first 4 bytes)
    length_data = client.recv(4)
    if len(length_data) < 4:
        print("Failed to receive the complete length of BSON document")
        return

    # Determine the expected length of the BSON document
    expected_length = int.from_bytes(length_data, byteorder='little')
    
    # Receive the rest of the BSON document based on its length
    bson_data = length_data + recvall(client, expected_length - 4)

    try:
        obj = decode(bson_data)
        parse_bson_obj(obj)
    except Exception as e:
        print(f"Error decoding BSON: {e}")
   

# Function to parse BSON object and publish data to RabbitMQ
def parse_bson_obj(obj):
    try:
        # Dictionary mapping data types to routing keys
        data_types = {
            'Documents': '.Document.',
            'Images': '.Image.',
            'Audio': '.Audio.',
            'Video': '.Video.'
        }

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        
        # Iterate through each data type and publish relevant items
        for data_type, routing_key in data_types.items():
            if obj[data_type]:
                for item in obj[data_type]:
                    # Prepare dashboard message with time
                    dashboard_message = {
                        'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                        'job_id': item['ID'],
                        'content_id': (item.get('ContentId') or item.get('PictureID') or 
                                     item.get('AudioID') or item.get('VideoID')),
                        'content_type': data_type.rstrip('s'),  # Remove 's' from end
                        'file_name': item['FileName'],
                        'status': 'Processed',
                        'message': f"{data_type.rstrip('s')} file '{item['FileName']}' successfully sent to {data_type} queue"
                    }

                    # Send to dashboard
                    channel.basic_publish(
                        exchange='',
                        routing_key='Dashboard',
                        body=encode(dashboard_message),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )

                    # Send original item to content queue
                    channel.basic_publish(
                        exchange='Topic',
                        routing_key=routing_key,
                        body=encode(item),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )

            else:
                print(f"No {data_type.lower()} to send")

        connection.close()

    except Exception as e:
        print(f"Error in parse_bson_obj: {e}")
        
        try:
            # Send error status to dashboard
            error_message = {
                'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                'status': 'Error',
                'message': str(e)
            }
            
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.basic_publish(
                exchange='',
                routing_key='Dashboard',
                body=bson.encode(error_message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
        except Exception as e2:
            print(f"Error sending error status: {e2}")

# Function to publish messages to RabbitMQ
def publish_to_rabbitmq(routing_key, message):
    try:
        # Establish a connection to the RabbitMQ server
        connection_parameters = pika.ConnectionParameters('localhost')
        connection = pika.BlockingConnection(connection_parameters)

        # Create a channel for communication with RabbitMQ
        channel = connection.channel()

        #prepping status message
        status_message = message.copy()
        del status_message['Payload'] #remove payload from status message
        status_message['Status'] = 'Preprocessed Successfully' 
        status_message['Message'] = 'Message has been preprocessed and sent to the respective queues' 

        
        status_message=encode(status_message)

        # Serialize the message to BSON
        message = encode(message)

        '''
            Sample message  to be sent to the respective queues
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Payload": "String"
            }
        '''
        # Publish the message to the specified routing key
        channel.basic_publish(
            exchange="Topic",
            routing_key=routing_key,
            body=message
        )
        '''
        This will be sent to the dashboard
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Status": "Preprocessed Successfully",
                "Message": "String"
            }
        '''
        #publish status message to dashboard
        channel.basic_publish(
            exchange="Topic",
            routing_key=".Status.",
            body=status_message
        )

    except Exception as e:
        '''
        This will be sent to the dashboard
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Status": "Preprocessing Failed",
                "Message": "String"
            }
        '''
        status_message = message.copy()
        del status_message['Payload']
        status_message['Status'] = 'Preprocessing Failed'
        status_message['Message'] = e
        status_message=encode(status_message)
        channel.basic_publish(
            exchange="Topic",
            routing_key=".Status.",
            body= status_message
        )
    # Close the connection to RabbitMQ
    connection.close()

# Function to start a socket server and listen for incoming BSON objects
def receive_bson_obj():
    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the socket to localhost on port 12345
        s.bind(('localhost', 12349))
        # Listen for incoming connections
        s.listen()

        # Continuously accept new connections
        while True:
            # Accept a connection
            conn, addr = s.accept()
            print('Connected by', addr)
            # Handle each client connection in a separate thread
            threading.Thread(target=handle_client, args=(conn,)).start()
    

# Main function to start the server
if __name__ == '__main__':
    receive_bson_obj()
    print("all message send")

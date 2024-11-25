import socket
from bson import BSON, encode, decode  # Binary JSON format
import threading  # For handling multiple clients concurrently
import pika  # RabbitMQ client library
from pika.exchange_type import ExchangeType
from copy import deepcopy  # Import deepcopy if you need a deep copy

def recvall(sock, expected_length):
    data = b''
    while len(data) < expected_length:
        more_data = sock.recv(expected_length - len(data))
        if not more_data:
            raise Exception("Socket closed before we received the complete document")
        data += more_data
    return data

def handle_client(client):
    try:
        length_data = client.recv(4)
        if len(length_data) < 4:
            print("Failed to receive the complete length of BSON document")
            return

        expected_length = int.from_bytes(length_data, byteorder='little')
        bson_data = length_data + recvall(client, expected_length - 4)
        
        # Decode BSON to dictionary
        obj = decode(bson_data)
        # Send the decoded dictionary
        publish_to_rabbitmq('.Status.', obj)
        
    except Exception as e:
        print(f"Error decoding BSON: {e}")
    finally:
        client.close()
   

# Function to publish messages to RabbitMQ
def publish_to_rabbitmq(routing_key, message):
    try:
        connection_parameters = pika.ConnectionParameters('localhost')
        connection = pika.BlockingConnection(connection_parameters)
        channel = connection.channel()

        # Encode the message in BSON
        bson_message = encode(message)

        channel.basic_publish(
            exchange="Topic",
            routing_key=routing_key,
            body=bson_message,
            properties=pika.BasicProperties(
                content_type='application/bson',
                delivery_mode=2  # Persistent message
            )
        )
        print("Message published successfully")
        connection.close()

    except Exception as e:
        print(f"Error publishing to RabbitMQ: {e}")
# Function to start a socket server and listen for incoming BSON objects
def receive_bson_obj():
    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the socket to localhost on port 12345
        s.bind(('localhost', 12346))
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


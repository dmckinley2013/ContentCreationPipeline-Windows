import socket
from bson import decode_all, BSON  # Corrected imports
import threading
import pika
from pika.exchange_type import ExchangeType
from copy import deepcopy

def recvall(sock, expected_length):
    data = b''
    while len(data) < expected_length:
        more_data = sock.recv(expected_length - len(data))
        if not more_data:
            raise Exception("Socket closed before we received the complete document")
        data += more_data
    return data

def handle_client(client):
    length_data = client.recv(4)
    if len(length_data) < 4:
        print("Failed to receive the complete length of BSON document")
        return

    expected_length = int.from_bytes(length_data, byteorder='little')
    bson_data = length_data + recvall(client, expected_length - 4)

    try:
        obj = decode_all(bson_data)[0]
        parse_bson_obj(obj)
    except Exception as e:
        print(f"Error decoding BSON: {e}")

def parse_bson_obj(obj):
    data_types = {
        'Documents': '.Document.',
        'Images': '.Image.',
        'Audio': '.Audio.',
        'Video': '.Video.'
    }
    
    for data_type, routing_key in data_types.items():
        if obj[data_type]:
            for item in obj[data_type]:
                publish_to_rabbitmq(routing_key, item)
        else:
            print(f"No {data_type.lower()} to send")

def publish_to_rabbitmq(routing_key, message):
    try:
        connection_parameters = pika.ConnectionParameters('localhost')
        connection = pika.BlockingConnection(connection_parameters)
        channel = connection.channel()

        status_message = message.copy()
        del status_message['Payload']
        status_message['Status'] = 'Preprocessed Successfully'
        status_message['Message'] = 'Message has been preprocessed and sent to the respective queues'

        status_message = BSON.encode(status_message)  # Use BSON.encode for BSON encoding
        message = BSON.encode(message)  # Use BSON.encode for BSON encoding

        channel.basic_publish(
            exchange="Topic",
            routing_key=routing_key,
            body=message
        )

        channel.basic_publish(
            exchange="Topic",
            routing_key=".Status.",
            body=status_message
        )

    except Exception as e:
        status_message = message.copy()
        del status_message['Payload']
        status_message['Status'] = 'Preprocessing Failed'
        status_message['Message'] = str(e)
        status_message = BSON.encode(status_message)
        channel.basic_publish(
            exchange="Topic",
            routing_key=".Status.",
            body=status_message
        )

    connection.close()

def receive_bson_obj():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 12345))
        s.listen()

        while True:
            conn, addr = s.accept()
            print('Connected by', addr)
            threading.Thread(target=handle_client, args=(conn,)).start()

if __name__ == '__main__':
    receive_bson_obj()

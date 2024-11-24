import socket
from bson import BSON, decode, encode
import threading
import pika
from pika.exchange_type import ExchangeType
from copy import deepcopy
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Initially, receive the length of the BSON document
        length_data = client.recv(4)
        if len(length_data) < 4:
            print("Failed to receive the complete length of BSON document")
            return

        # Get full document
        expected_length = int.from_bytes(length_data, byteorder='little')
        bson_data = length_data + recvall(client, expected_length - 4)

        # Decode BSON data before sending to RabbitMQ
        obj = decode(bson_data)
        publish_to_rabbitmq('.Status.', obj)  # Send decoded object

    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        client.close()

def parse_status_message(obj):
    try:
        # Prepare dashboard message
        dashboard_message = {
            'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
            'job_id': obj.get('JobID'),
            'content_id': obj.get('contentID'),
            'status': obj.get('Status', 'Unknown'),
            'details': obj.get('details'),
            'message': f"Status update received for job {obj.get('JobID')}"
        }

        # Send to RabbitMQ
        publish_to_rabbitmq('.Status.', dashboard_message)
        logging.info(f"Status message processed for job {obj.get('JobID')}")

    except Exception as e:
        logging.error(f"Error parsing status message: {e}")
        raise

def publish_to_rabbitmq(routing_key, message):
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Add timestamp if not present
        if 'time' not in message:
            message['time'] = datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')

        channel.basic_publish(
            exchange='Topic',
            routing_key=routing_key,
            body=str(message),  # Send as string instead of BSON
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='text/plain'  # Changed content type
            )
        )

        logging.info(f"Message published to {routing_key}")
        connection.close()

    except Exception as e:
        logging.error(f"Error publishing to RabbitMQ: {e}")
        try:
            error_message = {
                'time': datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                'status': 'Error',
                'message': str(e),
                'job_id': message.get('job_id', 'Unknown'),
                'content_id': message.get('content_id', 'Unknown')
            }
            
            temp_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            temp_channel = temp_conn.channel()
            
            temp_channel.basic_publish(
                exchange='Topic',
                routing_key='.Status.',
                body=str(error_message),  # Send as string
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='text/plain'
                )
            )
            temp_conn.close()
        except Exception as e2:
            logging.error(f"Failed to send error status: {e2}")

def receive_bson_obj():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 12346))
        s.listen(1)
        logging.info("Status server listening on localhost:12346")

        while True:
            try:
                conn, addr = s.accept()
                logging.info(f'Connected by {addr}')
                threading.Thread(target=handle_client, args=(conn,)).start()
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

if __name__ == '__main__':
    try:
        receive_bson_obj()
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
    except Exception as e:
        logging.error(f"Server error: {e}")
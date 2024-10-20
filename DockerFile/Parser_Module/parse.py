import socket
import bson
import pika

def recvall(sock, expected_length):
    data = b''
    while len(data) < expected_length:
        more_data = sock.recv(expected_length - len(data))
        if not more_data:
            raise Exception("Socket closed before receiving complete data")
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
        obj = bson.loads(bson_data)
        publish_to_rabbitmq('', obj)
    except Exception as e:
        print(f"Error decoding BSON: {e}")

def publish_to_rabbitmq(routing_key, message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='Dashboard', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='Dashboard',
            body=bson.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Published message: {message['FileName']}")
        connection.close()
    except Exception as e:
        print(f"Error publishing message to RabbitMQ: {e}")

def receive_bson_obj():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 12345))
        s.listen()
        while True:
            conn, addr = s.accept()
            print('Connected by', addr)
            handle_client(conn)

if __name__ == '__main__':
    receive_bson_obj()

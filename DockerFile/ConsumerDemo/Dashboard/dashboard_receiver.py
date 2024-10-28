import pika
import bson
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

def consumer_connection(queues):
    # Establish a connection to RabbitMQ server
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()

    # Start consuming from the queues without declaring them
    for queue_name in queues:
        # Directly consume from the queue without declaring it
        channel.basic_consume(
            queue=queue_name,
            auto_ack=True,
            on_message_callback=on_message_received
        )

    print("Dashboard Receiver Started Consuming from all queues")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.close()
        connection.close()

def on_message_received(ch, method, properties, body):
    try:
        # Decode the BSON message body
        message_data = bson.BSON.decode(body)
        logging.info(f"Received message from {method.routing_key}: {message_data}")
    except Exception as e:
        logging.error(f"Failed to decode message from {method.routing_key}: {e}")

# List of queues to listen to
queues = ['Audio', 'Document', 'Image']

if __name__ == '__main__':
    consumer_connection(queues)

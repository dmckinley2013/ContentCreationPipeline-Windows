import pika
import bson
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def consumer_connection(queues):
    # Establish a connection to RabbitMQ server
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()

    # Declare all queues and start consuming from them
    for queue_name in queues:
        # Add the 'x-queue-mode' argument for lazy queues
        arguments = {'x-queue-mode': 'lazy'} if queue_name == 'Audio' else {}

        # Declare the queue with additional arguments if necessary
        channel.queue_declare(queue=queue_name, durable=True, arguments=arguments)

        # Consume messages from the queue
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

        # Print the received message for debugging
        logging.info(f"Received message from {method.routing_key}: {message_data}")

    except Exception as e:
        logging.error(f"Failed to decode message: {e}")

# List of queues to listen to
queues = ['Dashboard', 'Audio', 'Document', 'Image']

if __name__ == '__main__':
    consumer_connection(queues)

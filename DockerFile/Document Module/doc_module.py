import spacy
import pdfplumber
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import os
import io 
from PIL import Image
import fitz
import pika
from bson import BSON, decode, encode
import json
from datetime import datetime
import random
import hashlib
import sys
from bson import ObjectId
from copy import deepcopy  

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Metadata_Module')))

from analyzer import entityRelationExtraction
from recNparse import MessageProcessor

# from image_module import ImageProcessor
FilePath = os.path.dirname(__file__)

def openFile(the_file,file_name,contentID):
    # Pass file to Meta and Convert file to Text
    Meta_file = Meta(the_file,file_name)
    Text_Summerizer, Keyword = ConvertFile_txt(the_file,file_name,contentID)
    return Meta_file, Text_Summerizer, Keyword

def Meta(the_file,file_name):
    with pdfplumber.open(the_file) as pdf:
        with open(FilePath + "/" + 'Meta.txt', 'w') as f:
            print(pdf.metadata, file=f)
            print(pdf.pages, file=f)
    
    # Open Meta.txt as binary
    with open(FilePath + "/" + 'Meta.txt', 'rb') as f:
        return f

def ConvertFile_txt(the_file,file_name,contentID):
    text_pdf = ''
    with pdfplumber.open(the_file) as pdf:
        for page in pdf.pages:
            text_pdf += page.extract_text()
    Summerizer_file = Text_Summerizer(text_pdf,file_name,contentID)
    Keyword_file = KeyWord(text_pdf)
    return Summerizer_file, Keyword_file

def Text_Summerizer(text_pdf,file_name,contentID):
    """
    Summarize the provided text, handling line breaks as separate sentences. 
    Return the summary as an array of sentences, save it to 'summary.txt', and print the sentences.
    """
    nlp = spacy.load('en_core_web_lg')
    
    # Split the text on '\n' and process each line separately
    text_lines = text_pdf.split('\n')
    doc = nlp(" ".join(text_lines))  # Re-combine the lines after splitting
    
    # Calculate word frequencies excluding stop words and punctuation
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in STOP_WORDS and word.text not in punctuation:
            word_frequencies[word.text.lower()] = word_frequencies.get(word.text.lower(), 0) + 1
    
    # Normalize word frequencies
    max_frequency = max(word_frequencies.values(), default=1)
    for word in word_frequencies:
        word_frequencies[word] /= max_frequency
    
    # Score sentences based on word frequencies
    sentence_scores = {}
    for sent in doc.sents:
        for word in sent:
            if word.text.lower() in word_frequencies:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word.text.lower()]
    
    # Select top sentences for summary
    select_length = int(len(list(doc.sents))*.6)  # Adjust the proportion of sentences as needed
    summary_sentences = nlargest(select_length, sentence_scores, key=sentence_scores.get)
    
    # Convert the selected sentences to a list of strings, handling each line as a separate sentence
    summary = []
    for sent in summary_sentences:
        # Split each sentence by '\n' to handle line breaks as separate sentences
        summary.extend([line.strip() for line in sent.text.split('\n') if line.strip()])
    
    # Save the summary to a text file
    summary_path = os.path.join(FilePath, "summary.txt")
    with open(summary_path, 'w') as f:
        for sentence in summary:
            f.write(sentence + '\n')
    
    # Print the summary sentences in a structured format
    print("Summary Sentences:")
    for sentence in summary:
        print(f"- {sentence}")

    entityRelationExtraction.analyze(summary,file_name,contentID)
    
    return summary


# def Text_Summerizer(text_pdf):
#     nlp = spacy.load('en_core_web_sm')
#     doc = nlp(text_pdf)
#     tokens = [token.text for token in doc]
#     word_frequencies = {}
#     for word in doc:
#         if word.text.lower() not in list(STOP_WORDS):
#             if word.text.lower() not in punctuation:
#                 if word.text not in word_frequencies.keys():
#                     word_frequencies[word.text] = 1
#                 else:
#                     word_frequencies[word.text] += 1
#     max_frequency = max(word_frequencies.values())
#     for word in word_frequencies.keys():
#         word_frequencies[word] = word_frequencies[word]/max_frequency
#     sentence_tokens = [sent for sent in doc.sents]
#     sentence_scores = {}
#     for sent in sentence_tokens:
#         for word in sent:
#             if word.text.lower() in word_frequencies.keys():
#                 if sent not in sentence_scores.keys():
#                     sentence_scores[sent] = word_frequencies[word.text.lower()]
#                 else:
#                     sentence_scores[sent] += word_frequencies[word.text.lower()]
#     select_length = int(len(sentence_tokens)*1)
#     summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)
#     final_summary = [word.text for word in summary]
#     summary = ''.join(final_summary)
#     with open(FilePath + "/" + "summary.txt", 'w') as f:
#         print(summary, file=f)
#     # Open summary.txt as binary
#     with open(FilePath + "/" + 'summary.txt', 'rb') as f:
#         return f

def KeyWord(text_pdf):
    nlp = spacy.load('en_core_web_lg')
    pos_tag = ['PROPN', 'ADJ', 'NOUN']  # 1
    doc = nlp(text_pdf.lower())  # 2
    result = []
    for token in doc:
       # 3
        if (token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
    # 4
        if (token.pos_ in pos_tag):
            result.append(token.text)
    with open(FilePath + "/" + "keywords_from_document.txt", 'w') as f:
        print(result, file=f)
    # Open keywords_from_document.txt as binary
    with open(FilePath + "/" + 'keywords_from_document.txt', 'rb') as f:
        return f

# iterate over PDF pages 
def IteratePDF(pdf_file_path,content_ID):
    
    pdf_file = fitz.open(pdf_file_path)
    image_len = 0
    for page_index, page in enumerate(pdf_file):
        image_list = page.get_images() 

        # printing number of images found in this page 
        if image_list: 
            print(f"[+] Found a total of {len(image_list)} images in page {page_index}") 
            image_len += 1
        else: 
            print("[!] No images found on page", page_index) 

        for image_index, img in enumerate(page.get_images(), start=1): 
            # get the XREF of the image 
            xref = img[0] 

            # extract the image bytes 
            base_image = pdf_file.extract_image(xref) 

            image_bytes = base_image["image"] 

            # get the image extension 
            image_ext = base_image["ext"] 

            # load it to PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Define the path to the images folder
            image_path = os.path.join(os.path.dirname(__file__), 'images')
            
            # Create the folder if it does not exist
            os.makedirs(image_path, exist_ok=True)
        
            # save it to local disk
            image.save(open(f"{image_path}/image{page_index+1}_{image_index}.{image_ext}", "wb"))
    #return amount of images
    return image_len


def remove_files():
    try:
        # Try to remove Meta.txt if it exists
        if os.path.exists(FilePath + "/" + 'Meta.txt'):
            os.remove(FilePath + "/" + 'Meta.txt')
        
        # Try to remove summary.txt if it exists
        if os.path.exists(FilePath + "/" + 'summary.txt'):
            os.remove(FilePath + "/" + 'summary.txt')
        
        # Try to remove keywords_from_document.txt if it exists
        if os.path.exists(FilePath + "/" + 'keywords_from_document.txt'):
            os.remove(FilePath + "/" + 'keywords_from_document.txt')
        
        # Check if images directory exists before trying to remove files
        images_path = os.path.join(FilePath, "images")
        if os.path.exists(images_path):
            # Remove all files in the images directory
            for file in os.listdir(images_path):
                file_path = os.path.join(images_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            # Optionally remove the empty images directory
            try:
                os.rmdir(images_path)
            except Exception as e:
                print(f"Could not remove images directory: {e}")
                
    except Exception as e:
        print(f"Error during file cleanup: {e}")
    
# Function to publish messages to RabbitMQ
def publish_to_rabbitmq(routing_key, message):
    # Establish a connection to the RabbitMQ server
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)

    # Create a channel for communication with RabbitMQ
    channel = connection.channel()
    
    status_message= message.copy()
    # if 'Payload' in message:
    #     del message['Payload']

    # # Log the message without Payload
    # print("Publishing message without Payload:", message)
    
    if 'PictureID' in status_message:
        status_message['status'] = 'Processed Successfully in Document Module'
        status_message['Message'] = 'Message has been Processed and sent to the Image Queue'
        del status_message['Payload']
    else:
        status_message['Status'] = 'Processed Successfully in Document Module'
        status_message['Message'] = 'Message has been Processed and sent to the Store Queue'
        del status_message['Payload']
        del status_message['Meta']
        del status_message['Summary']
        del status_message['Keywords']
        '''
        This will be sent to the dashboard
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Status": "Processed Successfully",
                "Message": "Message has been Processed and sent to the Store Queue"
            }
        '''
    contentIDtoSend = message.get('ContentId')
    if contentIDtoSend:
        print("Content ID before calling receiver:", contentIDtoSend)
    else:
        print("ContentID is missing from the status_message.")

    status_message=encode(status_message)
    peek = message.copy()
    del peek['Payload']
    print("Publishing message without Payload:", peek)

    # Serialize the message to BSON
    message = encode(message)
    

    # if 'Payload' in message:
    #     del message['Payload']

    # Log the message without Payload
    
    
    # Publish the message to the specified routing key
    channel.basic_publish(
        exchange="Topic",
        routing_key=routing_key,
        body=message
    )

    #publish status message to dashboard
    channel.basic_publish(
        exchange="Topic",
        routing_key=".Status.",
        body=status_message
    )


    # Close the connection to RabbitMQ
    connection.close()
    return contentIDtoSend

   


def consumer_connection(routing_key):
    # Establish a connection to RabbitMQ server
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)

    # Create a channel
    channel = connection.channel()

    # Declare a queue (queue names are generated based on the routing key)
    queue_name = routing_key

    # Consume messages from the queue
    a=channel.basic_consume(queue=queue_name, auto_ack=True,
        on_message_callback=on_message_received)
    
    print('Preprocess Starting Consuming')
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.close()
        connection.close()
        
def compute_unique_id(data_object):
    # Convert the object to a string
    data_str = str(encode(data_object))
    
    # Append the current date and time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    combined_data = data_str + current_time + str(random.random())
    
    # Generate SHA-256 hash
    unique_id = hashlib.sha256(combined_data.encode()).hexdigest()
    
    return unique_id
from pprint import pprint
def on_message_received(ch, method, properties, body):
    try:
            #load the bson object
        body = decode(body) #windows change
        print("\nReceived Message Structure:")
        print("-------------------------")
        # Filter out Payload and create a clean dictionary for display
        message_structure = {
            key: value 
            for key, value in body.items() 
            if key != "Payload"
        }
        pprint(message_structure, indent=2)
        print("-------------------------\n")

        #save the payload to a file
        with open(FilePath + "/" + body['FileName'], 'wb') as f:
            f.write(body['Payload'])

        #open the file and convert it to text
        Meta_file, Text_Summerizer, Keyword = openFile(FilePath + "/" + body['FileName'], body['FileName'],body['ContentId'])
        
        # Generate ContentId if it doesn't exist
        # if 'ContentId' not in body:
        #     body['ContentId'] = compute_unique_id(body)
        #     print(f"Generated new ContentId: {body['ContentId']}")
            
            
        Image_file = IteratePDF(FilePath + "/" + body['FileName'],body['ContentId'])


        if Image_file > 0:
            for file in os.listdir(FilePath+"/images"):
                _, ext = os.path.splitext(file)
                ext = ext.lstrip('.')  # Remove the leading dot from the extension
                with open(FilePath + "/images/" + file, 'rb') as f:
                    image_payload = f.read()
                    image = {
                        "time": datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'),
                        "job_id": body['ID'],
                        "content_id": body['ContentId'],
                        "content_type": "Image",
                        "file_name": file,
                        "status": "Processed",
                        "message": f"Image file '{file}' successfully sent to Image queue",
                        "_id": ObjectId(),
                        "Payload": image_payload
                    }
                    image['PictureID'] = compute_unique_id(image)
                    #send the image to the next module
                    publish_to_rabbitmq('.Image.', image)
        else:
            print('No images found in the document')


        with open('Meta.txt', 'rb') as f:
            file = f.read()
            body['Meta'] = file
            f.close()
        with open('summary.txt', 'rb') as f:
            file = f.read()
            body['Summary'] = file
            f.close()
        with open('keywords_from_document.txt', 'rb') as f:
            file = f.read()
            body['Keywords'] = file
            f.close()
        '''
        This will be sent to the store module
            {
                "ID": "ObjectID",  
                "DocumentId": "ObjectID",
                "DocumentType": "String",
                "FileName": "String",
                "Payload": "Binary"
                "Meta": "Binary",
                "Summary": "Binary",
                "Keywords": "Binary"
            }
        '''
    
        #send the document to the next module
        contentID = publish_to_rabbitmq('.Store.', body)
        processor = MessageProcessor()
        processor.consume_store(contentID)
        
        processor1 = MessageProcessor()
        processor1.consume_image(contentID)

        

    # Example usage: consume from the Store queue
    
      
        # processorImage = ImageProcessor(contentID)
        # processorImage.consume_image()

        #CALL IMAGE MODULE WITH CONTENT ID  
        # processor.image_store(contentID)
        #remove the files
        remove_files()
        #remove the file
        os.remove(FilePath + "/" + body['FileName'])
    except Exception as e:
        print(e)
        #send the error message to the dashboard
        status_message= body.copy()
        del status_message['Payload']
        status_message['Status'] = 'Processing Failed'
        status_message['Message'] = e
        status_message = encode(status_message)
        publish_to_rabbitmq(".Status.", status_message)

if __name__ == "__main__":
    # Start consuming messages from the queue
    consumer_connection('Document')
    
    

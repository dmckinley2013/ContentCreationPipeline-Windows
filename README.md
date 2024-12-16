**Software Downloads** Before
* Make sure you have python 3.12 or less 
* Install neo4j Desktop - https://neo4j.com/download/
* Install Docker Desktop
* Install MongoDB community eddition (keep the activation key) [Mongo Download](https://www.mongodb.com/docs/manual/administration/install-community/)
* Install MongoDb Compass [MongoDB Compass](https://www.mongodb.com/products/tools/compass)
* Install ollama if you are on mac and download the model llama2:7b



**Neo4j Desktop Setup**
* - Skip Registration if it prompts you to.
* [ Watch Video](https://youtu.be/c_hldeLPN0g) 
* username:neo4j
* password: 12345678


**MongoDB Set Up**
- Start MongoDB service
    - Mac:  mongod --dbpath ~/mongodb-data/db
    - Windows: if custom: mongod --dbpath "C:\path\to\your\mongodb-data\db"
        - if Default path: mongod --dbpath "C:\data\db"
-Open MongoDB Compass and click new connection
![image](https://hackmd.io/_uploads/HJf1-6jXyx.png)
and fill out the form as shown bellow.
mongodb://localhost:27017/dashboard_db
![image](https://hackmd.io/_uploads/r1F6yToQyg.png)

**Docker Desktop Setup**
- Run Docker Desktop

## Running the Docker Containers

Ensure **Docker Desktop** is running if you are on Windows.

1. **Start the Docker containers**:

    - For Windows or Gpu
   ```bash
   docker-compose --profile gpu up
   ```
   - For Mac or no Gpu
    ```bash
   docker-compose --profile non-gpu up
   ```
## Setting up the environment

1. **Create a virtual environment** (in the main project directory):
   ```bash
   python -m venv env
   ```
   for Mac
   ```bash
   python3 -m venv env
   ```

2. **Activate the virtual environment**:
   - On **Windows**:
     ```bash
     env\Scripts\activate
     ```
   - On **Mac/Linux**:
     ```bash
     source env/bin/activate
     ```

3. **Install dependencies** in the environment:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create/Train the Spacy Model** : Navigate to the Metadata_Module Folder
   ```bash
   python3 SpacyTraining.py
   ```
   This will create the folder containing the custom spacy Model. The Analyzer will use this model called "custom_ner_modelREL" or whatever the output file name is given in SpacyTraining.py
   

## Running the Python Scripts



1. **Start All services - Frontend and Backend**:
   Navigate to the directory where `run_all_macunix.py` or `run_all.py`  is located and run:
   ```bash
   python <filename.py>
   ```


2. **Open the Document Module** (open a new terminal):
-Before running if you are on a mac change line 28 to 
```from image_moduleMac import ImageClassifier```
on windows it should be 
```from image_module import ImageClassifier```

The reason for this is that we could not get Microsoft Resnet 50 running on Mac

   Navigate to the directory where `doc_module.py` is located and run:
   ```bash
   python doc_module.py
   ```

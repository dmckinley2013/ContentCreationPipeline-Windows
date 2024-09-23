#import packages put your Initials 
#from statusFeed import statusFeed importing the status feed file so we cn use the functions in here.
#-----------------------------------Isaam & Dylan--------------------------------------------#
#create a catch all Receiver 
#make it continously listen 

#This will receive all the files in the queue and save it to a local folder.. This receiver will check the document queue first.. Once it finds the first doc in waiting, it will look in all other queues (image, document, store etc )with the uniqueID associated with that document

#Create a local Directory with name uniqueID and save all files to that directory..


#function createDir{
#once files stores call the messageBuilder function with parameters 
#stausFeed.MessageBuilder() 



#this will send a msg dashboard saying "Files have been saved to storage" 

# function sendDataToAnalyzer {
 #call the analyzer function. 

# txtAnalyzer(*Pass the location of the summary text here /uniqueID/Summary.txt and ImageClassfier.txt if any) this 
# }
#-----------------------------------Dylan--------------------------------------------#

#build error handler if there is an error, collect log and put details in the details variable and call the messageBuilder Function

#-----------------------------------Akeno--------------------------------------------#

# def txt_analyzer (location_of_summary_txt: str, location_of_image_txt: str) -> list: {

#in here we will load text files from the location, extract relationships and pass to dbOpertations to create grpahNodes and edges and output to an array of strings 

#do we need to create an function to extract the mission profile of the digital twin and update DT object in DB


#structure (DigitalTwin -> Relation -> DigitalTwin, DigitalTwin -> Relation -> LearnerNode)
#arrayRelations["Jet -> powerplant-> GEJet", "GEJet -> learnerObject -> LearNode"]

#-----------------------------------Mohammad--------------------------------------------#
# def dbOperations (we'll figure out what format but pass the extracted relationships maybe an array of strings)
import traceback
import spacy
from spacy.tokens import Doc
from dbOperationsLocal import nodeBuilder
import copy

# Register a custom attribute for inferred relations
if not Doc.has_extension("relations"):
    Doc.set_extension("relations", default=[])

# Define the relationship extraction component
class TypeBasedRelationExtractor:
    def __call__(self, doc):
        entities = {"digitalTwinAircraft": [], "digitalTwinEngine": [],"digitalTwinElectricGenerator": [], "digitalTwinGround": [], "digitalTwinMarine":[]}
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent)

        relations = []
        for aircraft in entities["digitalTwinAircraft"]:
            for engine in entities["digitalTwinEngine"]:
                # relations.append({"relation": "has_engine", "head": aircraft.text, "tail": f" {engine.text}"})
                relations.append({"relation": "engine"})
        for ground in entities["digitalTwinGround"]:
            for engine in entities["digitalTwinEngine"]:
                # relations.append({"relation": "has_engine", "head": ground.text, "tail": f" {engine.text}"})
                 relations.append({"relation": "Engine"})
        for marine in entities["digitalTwinMarine"]:
            for engine in entities["digitalTwinEngine"]:
                # relations.append({"relation": "has_engine", "head": ground.text, "tail": f" {engine.text}"})
                 relations.append({"relation": "Engine"})
        for m in entities["digitalTwinMarine"]:
            for engine in entities["digitalTwinElectricGenerator"]:
                # relations.append({"relation": "has_engine", "head": ground.text, "tail": f" {engine.text}"})
                 relations.append({"relation": "ElectricGenerator"})
          
        # print("Relations:", relations)
        
        doc._.relations = relations
        return doc

# Register the custom component
@spacy.language.Language.factory("type_based_relation_extractor")
def create_type_based_relation_extractor(nlp, name):
    return TypeBasedRelationExtractor()

# Load the trained NER model and add the relationship extractor
nlp = spacy.load("Z:\BuildingTheDashboardModule_Group18-2\DockerFile\Metadata_Module\custom_ner_modelREL") #change to your custom directory
nlp.add_pipe("type_based_relation_extractor", last=True)


class entityRelationExtraction:

    
    def analyze(sentences,file_name):
        print("analyze() called from:")
        traceback.print_stack()  # This will show the call stack leading to analyze
        print(sentences)
        nodes = []

        learnerNode = [file_name, "learnerObject", "pdf"]
        learnerRelation = ["learnerObject"]


        # Define relationship map for node types
        relationship_map = {
            ("digitalTwinAircraft", "digitalTwinEngine"): "engine",
            ("digitalTwinEngine", "digitalTwinAircraft"): "engine",
            ("digitalTwinGround", "digitalTwinEngine"): "engine",
            ("digitalTwinEngine", "digitalTwinGround"): "engine",
            ("digitalTwinMarine", "digitalTwinEngine"): "engine",
            ("digitalTwinEngine", "digitalTwinMarine"): "engine",
            ("digitalTwinMarine", "digitalTwinElectricGenerator"): "generator",
             ("digitalTwinElectricGenerator", "digitalTwinMarine"): "generator",
            # Add more relationships as needed
        }
        entity_counts = {}
        for sentence in sentences:
            doc = nlp(sentence)
            
            
            for ent in doc.ents:
            
                print(f"Entity: {ent.text}, Label: {ent.label_}")
                
                #extracting the properties of the nodes  - the format is always digitalTwin(11 charcters) followed by whatever the digital twin may be. for example digitalTwinAircraft
                nodeType = ent.label_[:11] #digitalTwin
                digitalTwinType = ent.label_[11:] #after the 11th character is Aircraft
                currentNode = [ent.text, nodeType, digitalTwinType]

                # Add current node to nodes list
                nodes.append(currentNode)

                # This ensures that we ignore leading/trailing spaces and treat the entity text in a case-insensitive manner.
                normalized_entity = ent.text.strip().lower()
                # counts the number each entity appears
                entity_counts[normalized_entity] = entity_counts.get(normalized_entity, 0) + 1
                
                # Check for relation after every two nodes
                if len(nodes) >= 2:
                    # Get previous node and current node for relationship check
                    prev_node = nodes[-2]
                    current_node = nodes[-1]

                    # Extract their types to check relationship
                    prev_type = prev_node[1] + prev_node[2]
                    curr_type = current_node[1] + current_node[2]
                    relationship = relationship_map.get((prev_type, curr_type))

                    if relationship:
                        # Add relationship node if found in the map
                        relation_node = [relationship]
                        nodes.insert(len(nodes) - 1, relation_node)
        main_topic = None
        if entity_counts:
        # Select the most frequent entity from the counts
            main_topic = max(entity_counts, key=entity_counts.get)
        print(entity_counts)
        print(f"Main Topic: {main_topic}")
        print("Total Nodes:")
        print(nodes)
        
        # Remove duplicate nodes
        nodesUnique = remove_duplicate_nodes(nodes)
        print("Unique Nodes:")
        # Insert learnerNode and learnerRelation at the beginning of the nodes list
        main_topic_node_copy = find_main_topic_node(nodesUnique, main_topic)

        # combined_text = ''.join(sentences)
        # if len(combined_text) > 900:
        #     combined_text = combined_text[:900]
        # combined_text += "What is the {main_topic_node_copy[0]} and what does it do, Two sentence max"

    
        # missionProfile =  missionProfileExtraction(combined_text)
        # main_topic_node_copy.append(missionProfile)
        # print("MAIN HERE")
        # print(main_topic_node_copy)

        nodesUnique.insert(0, main_topic_node_copy)
        nodesUnique.insert(0, learnerRelation)
        nodesUnique.insert(0, learnerNode)

        print(nodesUnique)
        
        
        # Parse the nodes with relationships
  
        nodeBuilder.packageParser(nodesUnique)
def missionProfileExtraction(mainNode):
        import requests

        url = "http://127.0.0.1:5002/generate"

        # input_text = input("Enter Prompt: ")

        payload = {"input_text": mainNode}

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            generated_text = data.get("generated_text", "No text generated.")
            
            result = generated_text
            nodesArray = result
            print(nodesArray)
            print(result)  # Optional: Print it to verify
            return result
        else:
            print(f"Failed to connect to API: {response.status_code}")
            return

def find_main_topic_node(nodesUnique, main_topic):
    # Iterate over nodes to find the one containing the main topic
    for node in nodesUnique:
        # Check if the main topic is present in the node (specifically the first element, which seems to be the entity)
        if main_topic.lower() in node[0].lower():  # .lower() to handle case insensitivity
            # Make a copy of the node
            main_topic_node_copy = copy.deepcopy(node)  # Using deepcopy to make sure it's a true copy
            return main_topic_node_copy
    
    # Return None if no node is found with the main topic
    return None
def remove_duplicate_nodes(nodes):
    unique_nodes = []
    for node in nodes:
        if node not in unique_nodes:
            unique_nodes.append(node)
    print("Unique Nodes")
    print(unique_nodes)
    return unique_nodes

if __name__ == "__main__":
    # Example sentences for testing
    sentences = ["This is a test sentence."]
    entityRelationExtraction.analyze(sentences)
else:
    print(f"Module imported, __name__ is {__name__}")
from neo4j import GraphDatabase
from statusfeed1 import statusFeed


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "12345678")


def getAllNodes():
    with driver.session() as session:
        query = """MATCH (n) RETURN n LIMIT 100"""
        result = session.run(query)
        
        # Extract and print all nodes
        for record in result:
            node = record["n"]
            print(node)
   



def nodesRelation():
    # Create a driver instance
    driver = GraphDatabase.driver(URI, auth=AUTH)

    try:
        with driver.session() as session:
            nodeToLookFor = input(f"Enter the name of the node to search: ")

            # Query to find the node
            query = """MATCH (tNode:digitalTwin {name: $nodeToLookFor}) RETURN tNode"""
            result = session.run(query, {"nodeToLookFor": nodeToLookFor})

            found_any = False

            for record in result:
                tNode = record["tNode"]
                print("Node found:", tNode)  # Debugging: Print the node details
                found_any = True

                # Query for relationships from this node
                queryFindRelationFrom = """
                MATCH (tNode {name: $nodeName})-[r]->(connectedNode)
                RETURN tNode, type(r) AS relationshipType, connectedNode
                """

                # Run the query to find relationships
                resultNew = session.run(queryFindRelationFrom, {"nodeName": nodeToLookFor})

                # Print the relationships
                for relRecord in resultNew:
                    tNode = relRecord["tNode"]
                    relationshipType = relRecord["relationshipType"]
                    connectedNode = relRecord["connectedNode"]

                    print(f"Node: {tNode['name']} -> [{relationshipType}] -> {connectedNode['name']}")

            if not found_any:
                print("No Relationships were found")

    finally:
        # Ensure the driver is closed
        driver.close()

def nodeTraceback(learnerObject):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # The node to look for is passed as a parameter
        nodeToLookFor = learnerObject
        
        # Query to check if the node exists
        query = """MATCH (n {name: $nodeToLookFor}) RETURN n"""
        result = session.run(query, {"nodeToLookFor": nodeToLookFor})

        found_any = False
        printed_relationships = set()  # Set to track printed relationships
        relationMessage = []
        for record in result:
            tNode = record["n"]
            print("Node found:", tNode)  # Debugging: Print the node details
            found_any = True
            
            # Query to find all paths leading to and from the specified node
            queryFindRelations = """
            MATCH path = (node {name: $nodeToLookFor})-[*]-(connectedNode)
            RETURN node, nodes(path) AS nodeChain, relationships(path) AS relationChain
            """
            resultRelations = session.run(queryFindRelations, {"nodeToLookFor": nodeToLookFor})

            # Process each path and deduplicate relationships
            for path in resultRelations:
                nodeChain = path["nodeChain"]  # List of nodes along the path
                relationChain = path["relationChain"]  # List of relationships along the path

                for i in range(len(relationChain)):
                    fromNode = nodeChain[i]
                    toNode = nodeChain[i + 1]
                    relationshipType = relationChain[i].type  # Get the type of the relationship

                    # Ignore `learnerObject` relationships unless involving the specified node
                    if relationshipType in ["learnerObject_of", "has_learnerObject"]:
                        if nodeToLookFor not in [fromNode["name"], toNode["name"]]:
                            continue  # Skip irrelevant learnerObject relationships

                    # Normalize relationships for deduplication
                    relationship_key = tuple(sorted([fromNode["name"], toNode["name"]]))
                    relationship_string = (
                        f"{fromNode['name']} - [{relationshipType}] -> {toNode['name']}"
                        if fromNode["name"] == nodeToLookFor
                        else f"{toNode['name']} <- [{relationshipType}] - {fromNode['name']}"
                    )

                    # Print only if the relationship is unique
                    if (relationship_key, relationshipType) not in printed_relationships:
                        print(relationship_string)
                        printed_relationships.add((relationship_key, relationshipType))
                        
                        relationMessage.append(relationship_string)
        
        print(relationMessage)
        print("STATUS FEED CALLED HERE")
        statusFeed.messageBuilder(nodeToLookFor,"Nodes and relations have been stored to Neo4j ", relationMessage)        


        if not found_any:
            print("No node found with the specified name.")



def nodeTracebackManual():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # Get a partial node name from user input
        partialName = input("Enter part of the name of the node to search: ")
        
        # Query to find nodes with similar names
        queryFindSimilarNodes = """MATCH (n) WHERE n.name CONTAINS $partialName RETURN n"""
        result = session.run(queryFindSimilarNodes, {"partialName": partialName})

        # Collect matching nodes
        matching_nodes = []
        for record in result:
            matching_nodes.append(record["n"])

        # If no matching nodes are found
        if not matching_nodes:
            print(f"No nodes found with names containing '{partialName}'.")
            return

        # Present matching nodes to the user for selection
        print("Matching nodes found:")
        for idx, node in enumerate(matching_nodes):
            print(f"{idx + 1}. {node['name']}")

        # Let the user select a node
        while True:
            try:
                selection = int(input("Enter the number corresponding to the node you want to trace: "))
                if 1 <= selection <= len(matching_nodes):
                    selected_node = matching_nodes[selection - 1]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Use the selected node name for further processing
        nodeToLookFor = selected_node["name"]
        print(f"Tracing relationships for node: {nodeToLookFor}")

        # Query to find all paths connected to the selected node
        queryFindAllRelationships = """
        MATCH (fromNode)-[rel]-(toNode)
        WHERE fromNode.name = $nodeToLookFor OR toNode.name = $nodeToLookFor
        RETURN fromNode, rel, toNode
        """
        resultRelationships = session.run(queryFindAllRelationships, {"nodeToLookFor": nodeToLookFor})

        # Deduplicate and print relationships
        printed_relationships = set()
        relationMessage = []
        for record in resultRelationships:
            fromNode = record["fromNode"]
            toNode = record["toNode"]
            relationshipType = record["rel"].type

            # Normalize the relationship for deduplication
            relationship_key = tuple(sorted([fromNode["name"], toNode["name"]]))
            relationship_string = (
                f"{fromNode['name']} - [{relationshipType}] -> {toNode['name']}"
                if fromNode["name"] == nodeToLookFor
                else f"{toNode['name']} <- [{relationshipType}] - {fromNode['name']}"
            )

            # Add and print only unique normalized relationships
            if (relationship_key, relationshipType) not in printed_relationships:
                print(relationship_string)
                printed_relationships.add((relationship_key, relationshipType))
                relationMessage.append(relationship_string)
        print(relationMessage)


def updateNodes():
    with driver.session() as session:
        print("Executing query to find node with name ' GE414'...")
        nodeToLookFor = input(f"Enter the name of the node to update: ")
        # Query to find the node
        query = """MATCH (tNode:digitalTwin {name: $nodeToLookFor}) RETURN tNode"""
        result = session.run(query, {"nodeToLookFor": nodeToLookFor})

        found_any = False

        for record in result:
            tNode = record["tNode"]
            print("Node found:", tNode)  # Debugging: Print the node details
            found_any = True
            
            # Ask user for the new name
            newName = input(f"Enter the new name for the node: ")

            # Update query using the internal ID of the node to ensure you're updating the correct node
            queryUpdate = """
            MATCH (tNode) 
            SET tNode.name = $newName
            RETURN tNode
            """

            # Run the update query with the node ID and new name as parameters
            resultNew = session.run(queryUpdate, {"newName": newName})
            
            # Print the updated node
            for updatedRecord in resultNew:
                updatedNode = updatedRecord["tNode"]
                print("Updated Node:", updatedNode)

        if not found_any:
            print("No nodes were found with the name ' GE414'.")


#"node1+DT,relation,node2+LO"
#Node properties 
#digitalTwin
    #tmname:primaryNodeType(DT):SecondaryType(Aircraft,ship,etc): Properties MissionProfile, name
def addLearnerRelation(node1array, relation, node2array):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        learnerObject = node1array[1]
        mediaType = node1array[2]
        location = "TEST"
        contentID = "TEST"

        primaryType2 = node2array[1]
        secondaryType2 = node2array[2]
        missionProfile2 = "test"

        with driver.session() as session:
            query = f"""
                MERGE (node1:`{learnerObject}`:`{mediaType}` {{name: $nameofNode1, location: $location, contentID: $contentID}})
                MERGE (node2:`{primaryType2}`:`{secondaryType2}` {{name: $nameofNode2, missionProfile: $missionProfile2}})
                MERGE (node1)<-[:`has_{relation}`]-(node2)
                MERGE (node2)<-[:`{relation}_of`]-(node1)
            """
            session.run(query, {
                "nameofNode1": node1array[0],
                "nameofNode2": node2array[0],
                "location": location,
                "contentID": contentID,
                "missionProfile2": missionProfile2
            })


def addDigitalTwinRelation(node1array, relation, node2array):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        primaryType1 = node1array[1]
        secondaryType1 = node1array[2]
        missionProfile1 = "TEST"

        primaryType2 = node2array[1]
        secondaryType2 = node2array[2]
        missionProfile2 = "TEST"

        with driver.session() as session:
            query = f"""
                MERGE (node1:`{primaryType1}`:`{secondaryType1}` {{name: $nameofNode1}})
                MERGE (node2:`{primaryType2}`:`{secondaryType2}` {{name: $nameofNode2}})
                MERGE (node1)<-[:`has_{relation}`]-(node2)
                MERGE (node2)<-[:`{relation}_of`]-(node1)
            """
            session.run(query, {
                "nameofNode1": node1array[0],
                "nameofNode2": node2array[0]
                
            })

        # statusFeed.messageBuilder("TEST","Metadata has been stored to Neo4j ", "Details")
        # session.run(
        #     f"""
        #     MERGE (node1:digitalTwin {{name: $nameofNode1}})
        #     MERGE (node2:digitalTwin {{name: $nameofNode2}})
        #     MERGE (node1)<-[:{{$relationHas}}]-(node2)
        #     MERGE (node2)<-[:{{relationOf}}]-(node1)
        #     """,
        #     {
        #         "nameofNode1": node1,
        #         "nameofNode2": node2,
        #         "relationHas": "has_" + relation,
        #         "relationOf": relation + "_of"
        #     }
        # )
        # relString = node1 + " has the relationship of " + relation + " with " + node2
        # statusFeed.messageBuilder("123456","Metadata has been stored to Neo4j: " + relString, "N/A")


#Node properties 
#digitalTwin
    #tmname:primaryNodeType(DT):SecondaryType(Aircraft,ship,etc): Properties MissionProfile, name

#learnerObject
    #tname:primaryNodeType(LO):mediaType(pdf,img/jpeg,etc):Properties fileLocation:contentID

# with GraphDatabase.driver(URI, auth=AUTH) as driver:
#     nameOfNode = input('What is the node name? : ')
#     missionProfile = input('What is the Mission Profile? : ')
#     yearBuilt = input('What is the year built? : ')
#     create_digitalTwin(driver,nameOfNode,missionProfile,yearBuilt)




# nodes_relation = ["F18, ENGINE_OF, G414", "Boeing, ENGINE_OF, RR304"]

def store_relationship():
    relationships = []  # array to store relationships

    # First object input from user
    nameofNode1 = input("Enter object: ")

    # Loop
    while True:
        # Input for the relationship and the next object
        relationship = input(f"Enter the relationship for '{nameofNode1}': ")
        nameofNode2 = input(f"Enter the next object: ")

        # Stores and formats inputted string into the relationships list
        relationship_string = f"{nameofNode1},{relationship},{nameofNode2}"
        relationships.append(relationship_string)

        # Prompts user to enter more objects or end input
        additional_input = input("Do you want to add another object? (yes or no): ").lower()

        # Ends process if the user says 'no more'
        if additional_input == 'no':
            break

        # Moves to next object in the loop
        nameofNode1 = nameofNode2

    # Output the relationships and nodes array
    # print("Relationships and nodes array:")
    # print(relationships)
    return relationships

# 



class nodeBuilder:
    
    def packageParser(package):
        # with GraphDatabase.driver(URI, auth=AUTH) as driver:
            #node 0 is learner node 
            #index 1 is node 1 index 2 is relation index 3 is node 2 
            #  
            # updateNodes()
            # getAllNodes()
            # nodesArray = [nodes.split(",") for nodes in store_relationship()]
        learnerObject = package[0][0] #tracing the PDF 
     
        node1array = package[0]
        # print(node1array)
        relation = package[1][0]
        # print(relation)
        node2array = package[2]
        
        # print(node2array)
        addLearnerRelation(node1array, relation, node2array)
        del package[0:3] 

       
 # Remove 3 elements since node1array, relation, node2array are used

        counter = 0
        size = len(package)

        # Run the loop as long as there are at least 3 elements in the package
        while size >= 3:
            # print(f"Counter: {counter}")
            counter += 2

            node1array = package[0]
            # print(node1array)
            relation = package[1][0]
            # print(relation)
            node2array = package[2]
            addDigitalTwinRelation(node1array, relation, node2array)
            del package[0:2]  # Remove 3 elements for consistency

            # Update size after modifying package
            size = len(package)
        
        nodeTraceback(learnerObject)

             
            
               
            

if __name__ == "__main__":
    package = [['Tank.pdf', 'learnerObject', 'pdf'], ['learnerObject'], ['Titan65 engine', 'digitalTwin', 'Engine'], ['Titan65 engine', 'digitalTwin', 'Engine'], ['engine'], ['M551 Sheridan', 'digitalTwin', 'Ground'], ['In addition', 'digitalTwin', 'Aircraft']]
    
    # package = [['docName', 'learnerObject', 'pdf'],['learnerObject'], ['FE718 engine', 'digitalTwin', 'Engine']]
    nodeBuilder.packageParser(package)
    #mainNode = "Titan65 engine"
    #nodeTracebackManual() #This is for testing not when the analyzer calls very similiar function nodeTraceback which is used to send a message to the dashboard about the main node.
    # for eachItem in package:
    #     #assign variable here 
    #     node1, relation, node2 = eachItem
    #     #node1 = F22+DT+Aircraft
    #     node1array =  node1.split("+")
    #     node2array = node2.split("+")

    #     print(node1array)
    #     print(node2array)
    #     # print(node1)
    #     # print(node2)

    #     add2nodesRelation(driver,node1array,relation,node2array)
    # nodesRelation()
    # nodeTraceback()

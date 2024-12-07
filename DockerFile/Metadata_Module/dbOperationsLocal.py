from neo4j import GraphDatabase
from statusFeed import statusFeed


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "12345678")


def getAllNodes():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        query = """MATCH (n) RETURN n LIMIT 100"""
        result = session.run(query)

        # Extract and print all nodes
        for record in result:
            node = record["n"]
            print(node)

import logging
from neo4j import GraphDatabase, exceptions
from neo4j.exceptions import Neo4jError, CypherSyntaxError

def nodeTraceback(learnerObject, contentID):
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
    except exceptions.ServiceUnavailable as e:
        logging.error(f"Could not connect to the database: {e}")
        return

    with driver.session() as session:
        nodeToLookFor = learnerObject

        # Query to trace `learnerObject_of` and the next relationship in one direction
        query = """
        MATCH path = (startNode {name: $nodeToLookFor})-[:learnerObject_of]->(intermediateNode)-[nextRel]->(connectedNode)
        RETURN startNode, relationships(path) as rels, nodes(path) as nodes
        """
        try:
            result = session.run(query, {"nodeToLookFor": nodeToLookFor})
        except CypherSyntaxError as e:
            logging.error(f"Cypher syntax error: {e}")
            return
        except Neo4jError as e:
            logging.error(f"Neo4j error: {e}")
            return

        found_any = False
        printed_relationships = set()
        relationMessage = []

        for record in result:
            found_any = True
            relationships = record["rels"]
            path_nodes = record["nodes"]

            # Extract relationships and nodes
            for i in range(len(relationships)):
                fromNodeName = path_nodes[i]["name"]
                toNodeName = path_nodes[i + 1]["name"]
                relationshipType = relationships[i].type

                # Normalize relationships for deduplication
                relationship_key = tuple(sorted([fromNodeName, toNodeName]))
                relationship_string = (
                    f"{fromNodeName} - [{relationshipType}] -> {toNodeName}"
                )

                if (relationship_key, relationshipType) not in printed_relationships:
                    print(relationship_string)
                    printed_relationships.add((relationship_key, relationshipType))
                    relationMessage.append(relationship_string)

        relationMessageString = ", ".join(relationMessage)
        print("STATUS FEED CALLED HERE")
        statusFeed.messageBuilder(
            learnerObject,
            contentID,
            "Nodes and relations have been stored to Neo4j",
            relationMessageString,
        )

        if not found_any:
            logging.info("No node found with the specified name.")


def nodeTracebackManual():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # Get a partial node name from user input
        partialName = input("Enter part of the name of the node to search: ")

        # Query to find nodes with similar names
        queryFindSimilarNodes = (
            """MATCH (n) WHERE n.name CONTAINS $partialName RETURN n"""
        )
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
                selection = int(
                    input(
                        "Enter the number corresponding to the node you want to trace: "
                    )
                )
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
        resultRelationships = session.run(
            queryFindAllRelationships, {"nodeToLookFor": nodeToLookFor}
        )

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




# "node1+DT,relation,node2+LO"
# Node properties
# digitalTwin
# tmname:primaryNodeType(DT):SecondaryType(Aircraft,ship,etc): Properties MissionProfile, name
def addLearnerRelation(node1array, relation, node2array):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        learnerObject = node1array[1]
        mediaType = node1array[2]
        location = "TEST"
        contentID = node1array[3]

        primaryType2 = node2array[1]
        secondaryType2 = node2array[2]
        missionProfile2 = node2array[3]

        with driver.session() as session:
            query = f"""
                MERGE (node1:`{learnerObject}`:`{mediaType}` {{name: $nameofNode1, location: $location, contentID: $contentID}})
                MERGE (node2:`{primaryType2}`:`{secondaryType2}` {{name: $nameofNode2}})
                ON CREATE SET node2.missionProfile = $missionProfile2
                MERGE (node1)<-[:`has_{relation}`]-(node2)
                MERGE (node2)<-[:`{relation}_of`]-(node1)
            """
            session.run(
                query,
                {
                    "nameofNode1": node1array[0],
                    "nameofNode2": node2array[0],
                    "location": location,
                    "contentID": contentID,
                    "missionProfile2": missionProfile2,
                },
            )


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
            session.run(
                query, {"nameofNode1": node1array[0], "nameofNode2": node2array[0]}
            )


def addImageLearner(node1array, relation, mainContentID):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        learnerObject = node1array[1]
        mediaType = node1array[2]
        location = node1array[3]
        contentID = node1array[4]
        predictedClass = node1array[5]

        with driver.session() as session:
            query = f"""
                CREATE (node1:`{learnerObject}`:`{mediaType}` {{
                    name: $nameofNode1,
                    contentID: $contentID,
                    location: $location,
                    predictedClass: $predictedClass
                }})
                MERGE (node2 {{contentID: $mainContentID}})
                ON CREATE SET node2.missionProfile = $missionProfile2
                CREATE (node1)<-[:`has_{relation}`]-(node2)
                CREATE (node2)<-[:`{relation}_of`]-(node1)
            """

            session.run(
                query,
                {
                    "nameofNode1": node1array[0],
                    "contentID": contentID,
                    "location": location,
                    "predictedClass": predictedClass,
                    "mainContentID": mainContentID,
                    "missionProfile2": "Default Mission Profile",  # Update with actual mission profile if available
                },
            )
            
            print("STATUS FEED CALLED HERE")
            statusFeed.messageBuilder(
                node1array[0],
                mainContentID,
                "Images has been stored and classified",
                predictedClass,
            )



# nodes_relation = ["F18, ENGINE_OF, G414", "Boeing, ENGINE_OF, RR304"]



    

class nodeBuilder:
    def imagePackageParser(package, contentID):
        content_ID = contentID

        while package:  # Loop continues as long as package is not empty
            node1array = package[0]
            print("Node HERE")
            print(node1array)

            relation = "Image"

            addImageLearner(node1array, relation, content_ID)
            del package[0]  # Remove just the first element instead of slice

    def packageParser(package):
        # with GraphDatabase.driver(URI, auth=AUTH) as driver:
        # node 0 is learner node
        # index 1 is node 1 index 2 is relation index 3 is node 2
        #
        # updateNodes()
        # getAllNodes()
        # nodesArray = [nodes.split(",") for nodes in store_relationship()]
        print("Passed Package")
        print(package)

        contentID = package[0]
        del package[0]
        print("CONTENT MAN")
        print(contentID)
        learnerObject = package[0][0]  # tracing the PDF

        node1array = package[0]
        node1array.append(contentID)
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

        nodeTraceback(learnerObject, contentID)


if __name__ == "__main__":
    package = ['378c2714e54e3ffb7fd98c9988e7d95ef8137bfdf0d9a99d229e005291e57448', 
               ['USSConstitutionRx900Steam.pdf', 'learnerObject', 'pdf'], 
               ['learnerObject'], 
               ['USS Constitution', 'digitalTwin', 'Marine', 'The USS Constitution is a historical United States Navy frigate that was launched in 1797 and is now a museum ship in Boston, Massachusetts. The USS Constitution serves as a symbol of American independence and naval power, and it continues to be an important cultural and historical artifact.'], 
               ['Fuel system', 'digitalTwin', 'Aircraft'], 
               ['USS Constitution', 'digitalTwin', 'Marine'], 
               ['engine'], 
               ['RX900 turbines', 'digitalTwin', 'Engine']]
    
    package1 = ['a0642259cd4014ae092b14ed65e4258352ca6cbc877b7b86a7cbccb9a00661e7', 
                ['GE414 Diff Sentence Structure.pdf', 'learnerObject', 'pdf'], 
                ['learnerObject'], 
                ['GE414 engine', 'digitalTwin', 'Engine', 'The GE414 is a high-performance engine developed by General Electric (GE) for use in aircraft. It is a two-spool turbofan engine that produces 14,000 pounds of thrust and is known for its reliability and efficiency.'], 
                ['GE414 engine', 'digitalTwin', 'Engine'],
                ['engine'], 
                ['F18 aircraft', 'digitalTwin', 'Aircraft'], 
                ['Fuel system', 'digitalTwin', 'Aircraft'], 
                ['TCarbonX', 'digitalTwin', 'Engine'], 
                ['GE414 require', 'digitalTwin', 'Engine']]
    
    package2= ['488b74ced1f1bc34c8a339668ff8cb87385c94fb5807d7e2f5c58d869a57ad4b', 
               ['F18GeEngineWithPic.pdf', 'learnerObject', 'pdf'], 
               ['learnerObject'], 
               ['GE414 engine', 'digitalTwin', 'Engine', 'The GE414 is a high-speed computing engine developed by General Electric (GE) for use in various applications, including weather forecasting, scientific simulations, and data analytics. The GE414 engine offers enhanced performance and scalability compared to its predecessor, the GE350, and is designed to support complex workloads and large datasets with ease.'], 
               ['GE414 engine', 'digitalTwin', 'Engine'], 
               ['engine'], 
               ['F18 aircraft', 'digitalTwin', 'Aircraft'], 
               ['TCarbonX', 'digitalTwin', 'Engine']]
    # nodeBuilder.packageParser(package)
    nodeTracebackManual()
    # getAllNodes()
    # nodeBuilder.packageParser(package)
    # imagePackage = [
    #     "Test Image 3",
    #     "learnerObject",
    #     "Image",
    #     "Location_path",
    #     "22",
    #     "PredictedClass",
    # ]
    # nodeBuilder.imagePackageParser(
    #     imagePackage, "1f8f41bd0ea9214b93c834cc4e28209191a2964101fdc84c823b9b9191b5ead6"
    # )


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

        query = """
        MATCH (node {name: $nodeToLookFor})-[r]-(connectedNode)
        WHERE NOT (type(r) IN ['has_Image', 'Image_of'])
          AND (
            NOT (type(r) IN ['learnerObject_of', 'has_learnerObject']) 
            OR $nodeToLookFor IN [node.name, connectedNode.name]
          )
        RETURN node, r, connectedNode
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
            node = record["node"]
            r = record["r"]
            connectedNode = record["connectedNode"]

            relationshipType = r.type
            fromNodeName = node["name"]
            toNodeName = connectedNode["name"]

            # Normalize relationships for deduplication
            relationship_key = tuple(sorted([fromNodeName, toNodeName]))
            relationship_string = (
                f"{fromNodeName} - [{relationshipType}] -> {toNodeName}"
                if fromNodeName == nodeToLookFor
                else f"{toNodeName} <- [{relationshipType}] - {fromNodeName}"
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
    package = [
        ["Tank.pdf", "learnerObject", "pdf"],
        ["learnerObject"],
        ["Titan65 engine", "digitalTwin", "Engine"],
        ["Titan65 engine", "digitalTwin", "Engine"],
        ["engine"],
        ["M551 Sheridan", "digitalTwin", "Ground"],
        ["In addition", "digitalTwin", "Aircraft"],
    ]

    
    # nodeBuilder.packageParser(package)
    imagePackage = [
        "Test Image 3",
        "learnerObject",
        "Image",
        "Location_path",
        "22",
        "PredictedClass",
    ]
    nodeBuilder.imagePackageParser(
        imagePackage, "1f8f41bd0ea9214b93c834cc4e28209191a2964101fdc84c823b9b9191b5ead6"
    )


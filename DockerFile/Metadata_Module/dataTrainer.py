import spacy

# Load a blank English model
nlp = spacy.blank("en")

# Input array of sentences
sentences = [
    "MG78 turbine section.",
    "MG78 turbine section.",
    "MG78 turbine section.",
    "The GE414 engine powers the F18 aircraft.",
    "The GE54 engine powers the F16 aircraft.",
    "The F16 aircraft is equipped with a GE401 engine.",
    "The F18 aircraft requires regular maintenance for its GE534 engine.",
    "The M761 tank uses a Titan65 engine.",
    "The Titan65 engine is a high-performance model.",
    "The M761 tank uses a Titan65 engine.",
    "The F22 aircraft features the advanced GE556 engine.",
    "Regular maintenance is required for the Titan65 engine and the M761 tank.",
    "The GE414 engine is used in both commercial and military aircraft.",
    "The M551 tank is equipped with a powerful Titan88 engine.",
    "Titan88 engines are known for their durability in harsh conditions.",
    "The M551 tank uses a GE404 engine for enhanced performance.",
    "Maintenance for the F16 aircraft includes checking the GE554 engine.",
    "The M761 tank is built to withstand tough conditions, using the Titan65 engine.",
    "The F35 aircraft relies on the GE600 engine for superior performance.",
    "The M551 tank with the new GE509 engine has significantly improved its power.",
    "The GE509 engine powers various vehicles, including tanks and aircraft.",
    "The F16 aircraft and the F18 aircraft both use GE414 engines.",
    "The M761 tank and the M551 tank rely on different engines, including the Titan65.",
    "GE900 engines are used in the latest aircraft models for superior power.",
    "The F22 aircraft and the F35 aircraft both utilize GE600 engines for enhanced speed.",
    "Titan88 engines have been used in both the M551 and M761 tanks.",
    "The GE509 engine is a newly developed model for modern military vehicles.",
    "Routine checks for the F35 aircraft involve inspecting the GE600 engine.",
    "The turbine is in good condition.",
    "Torque settings",
    "Regular maintenance of the compressor is required.",
    "The DG5000 steam generators on the USS Missouri battleship play a critical role in providing reliable electricity for the ship’s operations.",
    "The DG5000 generators, responsible for electricity generation",
    "The STFD650 steam turbines power the USS Missouri",
    "The STFD650 steam turbines is the engine of the USS Missouri"
]




# Input array of phrases to index with their labels

phrases_to_index = {
    "GE414 engine": "digitalTwinEngine",
    "F18 aircraft": "digitalTwinAircraft",
    "GE54 engine": "digitalTwinEngine",
    "F16 aircraft": "digitalTwinAircraft",
    "GE401 engine": "digitalTwinEngine",
    "GE534 engine": "digitalTwinEngine",
    "M761 tank": "digitalTwinGround",
    "Titan65 engine": "digitalTwinEngine",
    "F22 aircraft": "digitalTwinAircraft",
    "GE556 engine": "digitalTwinEngine",
    "M551 tank": "digitalTwinGround",
    "Titan88 engine": "digitalTwinEngine",
    "GE404 engine": "digitalTwinEngine",
    "GE554 engine": "digitalTwinEngine",
    "F35 aircraft": "digitalTwinAircraft",
    "GE600 engine": "digitalTwinEngine",
    "GE509 engine": "digitalTwinEngine",
    "GE900 engine": "digitalTwinEngine",
    "DG5000 steam generators": "digitalTwinElectricGenerator",
    "USS Missouri battleship": "digitalTwinMarine",
    "STFD650 steam turbines": "digitalTwinEngine"
}
# Initialize a list to store training data
training_data = []

# Process each sentence
for sentence in sentences:
    doc = nlp(sentence)
    entities = []

    # Search for each phrase in the sentence
    for phrase, label in phrases_to_index.items():
        start_index = sentence.find(phrase)
        if start_index != -1:
            # Calculate the end index of the phrase
            end_index = start_index + len(phrase)
            entities.append((start_index, end_index, label))

    # Add the sentence and its entities to the training data
    training_data.append((sentence, {"entities": entities}))

# Print the final training data
print("\nTraining Data:")
for data in training_data:
    print(f"{data},")
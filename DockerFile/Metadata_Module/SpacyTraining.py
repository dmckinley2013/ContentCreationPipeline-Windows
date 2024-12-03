import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from spacy.tokens import Doc

# Step 1: Train the NER model

# Create a blank English model
nlp = spacy.blank("en")

# Create the NER component if it doesn't already exist
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# Training data with entities (no relationships here for NER training)
# TRAIN_DATA = [
#     ("The GE414 engine powers the F18 aircraft.", {"entities": [(4, 16, "digitalTwinEngine"), (28, 40, "digitalTwinAircraft")]}),
#     ("The F16 aircraft is equipped with a GE401 engine.", {"entities": [(4, 16, "digitalTwinAircraft"), (36, 48, "digitalTwinEngine")]}),
#     # Add other examples as needed...
# ]

TRAIN_DATA = [
    ("MG78 turbine section.", {"entities": []}), 
       ("MG78 turbine section.", {"entities": []}), 
          ("MG78 turbine section.", {"entities": []}), 
        ("The GE414 engine powers the F18 aircraft.", {"entities": [(4, 16, "digitalTwinEngine"), (28, 40, "digitalTwinAircraft")]}),
    ("The GE54 engine powers the F16 aircraft.", {"entities": [(4, 15, "digitalTwinEngine"), (27, 39, "digitalTwinAircraft")]}),
    ("The F16 aircraft is equipped with a GE401 engine.", {"entities": [(4, 16, "digitalTwinAircraft"), (36, 48, "digitalTwinEngine")]}),
    ("The F18 aircraft requires regular maintenance for its GE534 engine.", {"entities": [(4, 16, "digitalTwinAircraft"), (54, 66, "digitalTwinEngine")]}),
    ("The M761 tank uses a Titan65 engine.", {"entities": [(21, 28, "digitalTwinEngine"), (4, 13, "digitalTwinGround")]}),
    ("The Titan65 engine is a high-performance model.", {"entities": [(4, 18, "digitalTwinEngine")]}),
    ("The M761 tank uses a Titan65 engine.", {"entities": [(4, 13, "digitalTwinGround"), (21, 35, "digitalTwinEngine")]}),

    # New data
    ("The F22 aircraft features the advanced GE556 engine.", {"entities": [(4, 16, "digitalTwinAircraft"), (39, 51, "digitalTwinEngine")]}),
    ("Regular maintenance is required for the Titan65 engine and the M761 tank.", {"entities": [(40, 54, "digitalTwinEngine"), (63, 72, "digitalTwinGround")]}),
   
    ("The GE414 engine is used in both commercial and military aircraft.", {"entities": [(4, 16, "digitalTwinEngine")]}),
    ("The M551 tank is equipped with a powerful Titan88 engine.", {"entities": [(4, 13, "digitalTwinGround"), (42, 56, "digitalTwinEngine")]}),
    ("Titan88 engines are known for their durability in harsh conditions.", {"entities": [(0, 15, "digitalTwinEngine")]}),
    ("The M551 tank uses a GE404 engine for enhanced performance.", {"entities": [(4, 13, "digitalTwinGround"), (21, 33, "digitalTwinEngine")]}),
    ("Maintenance for the F16 aircraft includes checking the GE554 engine.", {"entities": [(20, 32, "digitalTwinAircraft"), (55, 67, "digitalTwinEngine")]}),
    ("The M761 tank is built to withstand tough conditions, using the Titan65 engine.", {"entities": [(4, 13, "digitalTwinGround"), (64, 78, "digitalTwinEngine")]}),
    ("The F35 aircraft relies on the GE600 engine for superior performance.", {"entities": [(4, 16, "digitalTwinAircraft"), (31, 43, "digitalTwinEngine")]}),
    
    ("The M551 tank with the new GE509 engine has significantly improved its power.", {"entities": [(4, 13, "digitalTwinGround"), (27, 39, "digitalTwinEngine")]}),
    ("The GE509 engine powers various vehicles, including tanks and aircraft.", {"entities": [(4, 16, "digitalTwinEngine")]}),
    ("The F16 aircraft and the F18 aircraft both use GE414 engines.", {"entities": [(4, 16, "digitalTwinAircraft"), (25, 37, "digitalTwinAircraft"), (47, 60, "digitalTwinEngine")]}),
    ("The M761 tank and the M551 tank rely on different engines, including the Titan65.", {"entities": [(4, 13, "digitalTwinGround"), (22, 31, "digitalTwinGround"), (73, 80, "digitalTwinEngine")]}),
    ("GE900 engines are used in the latest aircraft models for superior power.", {"entities": [(0, 13, "digitalTwinEngine")]}),
    ("The F22 aircraft and the F35 aircraft both utilize GE600 engines for enhanced speed.", {"entities": [(4, 16, "digitalTwinAircraft"), (25, 37, "digitalTwinAircraft"), (51, 64, "digitalTwinEngine")]}),
    ("Titan88 engines have been used in both the M551 and M761 tanks.", {"entities": [(0, 15, "digitalTwinEngine"), (43, 47, "digitalTwinGround"), (52, 62, "digitalTwinGround")]}),
    ("The GE509 engine is a newly developed model for modern military vehicles.", {"entities": [(4, 16, "digitalTwinEngine")]}),
    ("Routine checks for the F35 aircraft involve inspecting the GE600 engine.", {"entities": [(23, 35, "digitalTwinAircraft"), (59, 71, "digitalTwinEngine")]}),
     ("The turbine is in good condition.", {"entities": []}),
     ('Torque settings', {'entities': []}),
    ("Regular maintenance of the compressor is required.", {"entities": []}),
    ('The DG5000 steam generators on the USS Missouri battleship play a critical role in providing reliable electricity for the ship’s operations.', {'entities': [(4, 27, 'digitalTwinElectricGenerator'), (35, 47, 'digitalTwinMarine')]}),
    ('The DG5000 generators, responsible for electricity generation', {'entities': [(4, 21, 'digitalTwinElectricGenerator')]}),
    ('The STFD650 steam turbines power the USS Missouri', {'entities': [(4, 26, 'digitalTwinEngine'), (37, 49, 'digitalTwinMarine')]}),
    ('The STFD650 steam turbines is the engine of the USS Missouri', {'entities': [(4, 26, 'digitalTwinEngine'), (48, 60, 'digitalTwinMarine')]})

    

    
]


# Add labels to the NER component
for _, annotations in TRAIN_DATA:
    for ent in annotations.get("entities"):
        ner.add_label(ent[2])

# Disable other pipes for training
unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

# Train the NER model
with nlp.disable_pipes(*unaffected_pipes):
    optimizer = nlp.begin_training()
    for iteration in range(100):  # 30 iterations, adjust as needed
        losses = {}
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
        for batch in batches:
            examples = []
            for text, annotations in batch:
                # Create a Doc object and Example object
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)

            # Update the model with the Example objects
            nlp.update(examples, drop=0.5, losses=losses)

        print(f"Iteration {iteration + 1} Losses: {losses}")

# Save the trained NER model
nlp.to_disk("./custom_ner_modelREL")

# Step 2: Define the Relationship Extraction Component


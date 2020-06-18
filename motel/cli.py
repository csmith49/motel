import orm
import click
import log
import img
from motifs import Motif
from os import path
import json
import analysis

logger = log.get("cli")

# utility for connecting to a database
# def connect(db_path):
#     logger.info(f"Initiating connection to {db_path}...")
#     orm.db.bind(provider='sqlite', filename=path.abspath(db_path), create_db=True)
#     orm.db.generate_mapping(create_tables=True)
#     logger.info(f"Connection to {db_path} established.")

# entry point for the cli
@click.group()
def run(): pass

# make a database from a single document
@run.command()
def test():
    print("Motel requirements installed and loaded successfully.")

@run.command()
@click.argument("input", type=str, required=True)
@click.argument("output", type=str, default=":memory:")
def process(input, output):
    import nlp
    # connect to the output db (defaults to in-memory)
    with orm.Connection(output):
    # read the provided doc and process all the lines
        logger.info(f"Processing file {input}...")
        with open(input, "r") as f:
            text = f.read()
            nlp.process(text)
        logger.info(f"Processing of file {input} complete.")

@run.command()
@click.argument("input", type=str, required=True)
@click.argument("output", type=str, required=True)
def extract_neighborhoods(input, output):
    # connect to the doc
    with orm.Connection(input):
        # find all nodes with "user:label" and return the node/label pair to stdout
        logger.info(f"Looking for labels in {input}...")
        with orm.db_session:
            with open(output, "w") as f:
                logger.info(f"Writing results to {output}...")
                for vertex in orm.positive_vertices():
                    logger.info(f"Found vertex {vertex.id} with positive label. Constructing neighborhood...")
                    vertices, edges = orm.neighborhood(vertex, distance=2)
                    json_rep = {
                        "structure" : {
                            "vertices" : [v.to_json(avoid=["user:label"]) for v in vertices],
                            "edges" : [e.to_json() for e in edges]
                        },
                        "selector" : vertex.id
                    }
                    logger.info(f"Neighborhood for vertex {vertex.id} constructed.")
                    f.write(json.dumps(json_rep))
                    f.write("\n")
                logger.info(f"Results written to {output}.")

@run.command()
@click.argument("motifs", type=str, required=True)
@click.argument("data", type=str, required=True)
def evaluate(motifs, data):
    # generate the image and load the motifs
    image = img.SparseImage()
    with open(motifs, "r") as f:
        logger.info(f"Loading motifs from {motifs}...")
        motifs = [Motif.of_string(line) for line in f.readlines()]
        logger.info(f"Motifs loaded. Found {len(motifs)} motifs.")
    image.register_motifs(*motifs)
    # evaluate
    image.evaluate_motifs(data)
    image.dump("test.jsonl")

@run.command()
@click.argument("image", type=str, required=True)
@click.argument("output", type=str, required=True)
def analyze_image(image, output):
    # load the sparse image file from MotE
    motifs = analysis.load_motifs(image)
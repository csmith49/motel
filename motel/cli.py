import orm
import click
import log
from os import path
import json

logger = log.get("cli")

# utility for connecting to a database
def connect(db_path):
    logger.info(f"Initiating connection to {db_path}...")
    orm.db.bind(provider='sqlite', filename=path.abspath(db_path), create_db=True)
    orm.db.generate_mapping(create_tables=True)
    logger.info(f"Connection to {db_path} established.")

# entry point for the cli
@click.group()
def run(): pass

# make a database from a single document
@run.command()
@click.argument("input", type=str, required=True)
@click.argument("output", type=str, required=True)
def to_sql(input, output):
    connect(output)

@run.command()
def test():
    print("Motel requirements installed and loaded successfully.")

@run.command()
@click.argument("input", type=str, required=True)
@click.argument("output", type=str, default=":memory:")
def process(input, output):
    import nlp
    # connect to the output db (defaults to in-memory)
    connect(output)
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
    connect(input)
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
            logger.info(f"Results written to {output}.")
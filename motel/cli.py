import orm
import nlp
import click
import log

logger = log.get("cli")

# utility for connecting to a database
def connect(db_path):
    logger.info(f"Initiating connection to {db_path}...")
    orm.db.bind(provider='sqlite', filename=db_path, create_db=True)
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
    # connect to the output db (defaults to in-memory)
    connect(output)
    # read the provided doc and process all the lines
    logger.info(f"Processing file {input}...")
    with open(input, "r") as f:
        text = f.read()
        nlp.process(text)
    logger.info(f"Processing of file {input} complete.")
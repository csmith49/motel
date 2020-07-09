"""Command-line interface for Motel."""

import orm, log, img, doc, ensembles, stats
import click
from motifs import Motif
from os import path
import json, csv

logger = log.get("cli")

# entry point for the cli
@click.group()
@click.option("--quiet", is_flag=True)
def run(quiet):
    """Entry point for the CLI."""
    # if the quiet flag is passed, disable logging to stdout
    if quiet:
        log.enable_quiet_mode()

# make a database from a single document
@run.command()
def test():
    """Test command.

    Notes
    -----
    Only intended to ensure all modules (sans `nlp`) are imported correctly.

    When run, prints "Motel requirements installed and loaded successfully." to standard output.
    """
    print("Motel requirements installed and loaded successfully.")

@run.command()
@click.option("-i", "--input", type=str, required=True)
@click.option("-o", "--output", type=str, default=":memory:")
def process(input, output):
    """Convert a text file to a document.

    Parameters
    ----------
    input : str
        Filepath for the input text file.
    
    output : str, optional
        Filepath for the output document database. If none provided, defaults to an in-memory database.

    See Also
    --------
    `nlp.process` - the core functionality of this command-line procedure.
    """
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
@click.option("-i", "--input", type=str, required=True)
@click.option("-o", "--output", type=str, required=True)
def extract_neighborhoods(input, output):
    """Generates neighborhoods around labeled points in a set of documents.

    Parameters
    ----------
    input : str
        Filepath for the input data set.

    output : str
        Filepath for the output JSONL file.

    See Also
    --------
    `orm.neighborhood` - the critical functionality of this command-line process.
    """
    # load the data set
    dataset = doc.Dataset.load(input)
    for document in dataset.documents_by_split(doc.Split.TRAIN):
        with document.connect():
            # find all nodes with "user:label" and return the node/label pair to stdout
            logger.info(f"Looking for labels in {document.filepath}...")
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
@click.option("-m", "--motifs", type=str, required=True)
@click.option("-d", "--documents", type=str, required=True)
@click.option("-o", "--output", type=str, required=True)
def evaluate_motifs(motifs, documents, output):
    """Evaluates a set of motifs on a set of documents.

    Parameters
    ----------
    motifs : str
        Filepath for the JSONL file storing the motifs-to-be-evaluated.

    documents : str
        Filepath for the JSONL file storing the filepaths for the documents-to-be-evaluted.

    output : str
        Filepath for the resulting `SparseImage` object to be written to.

    See Also
    --------
    `image.evaluate_motifs` - the core functionality for this command-line process.

    """
    # generate the image and load the motifs
    image = img.SparseImage()
    with open(motifs, "r") as f:
        logger.info(f"Loading motifs from {motifs}...")
        motifs = [Motif.of_string(line) for line in f.readlines()]
        logger.info(f"Motifs loaded. Found {len(motifs)} motifs.")
    image.register_motifs(*motifs)
    # load the document list
    logger.info(f"Loading data set from {documents}...")
    dataset = doc.Dataset.load(documents)
    logger.info(f"Data set loaded. Found {len(dataset.documents)} documents.")
    # evaluate
    for document in dataset.documents:
        image.evaluate_motifs(document)
    # and write the results
    image.dump(output)

@run.command()
@click.option("-i", "--image", type=str, required=True)
@click.option("-d", "--documents", type=str, required=True)
@click.option("-o", "--output", type=str, default="")
@click.option("-t", "--thresholds", type=int, default=5)
@click.option("-a", "--active-learning-steps", type=int, default=10)
def evaluate(image, documents, output, thresholds, active_learning_steps):
    # load the data
    logger.info(f"Evaluating ensembles on {image} and {documents}...")
    logger.info("Loading assets...")
    image = img.SparseImage.load(image)
    dataset = doc.Dataset.load(documents)
    logger.info(f"Assets ({len(image.motifs)} motifs and {len(dataset.documents)} documents) loaded.")
    logger.info("Beginning evaluation...")
    results = []
    # step 1 - disjunction
    results += stats.evaluate_disjunction(image, dataset)
    # step 2 - majority vote
    results += stats.evaluate_majority_vote(image, dataset, thresholds=thresholds)
    # step 3 - weighted vote
    results += stats.evaluate_weighted_vote(image, dataset, active_learning_steps=active_learning_steps)
    # print out results to output
    if output:
        logger.info(f"Initiating writing output to {output}...")
        with open(output, "w") as f:
            writer = csv.DictWriter(f, fieldnames=stats.result_header)
            writer.writeheader()
            writer.writerows(results)
    logger.info("Ensemble evaluation done.")
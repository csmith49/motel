"""Document-level information and statistics."""

from img import Point
from orm import Connection, positive_vertices
import json

class Document:
    """A document database.

    Parameters
    ----------
    json_representation : dict
        A JSON-like representation of the document's filepath and other metadata.

    Attributes
    ----------
    filepath : str
        Filepath pointing to the document's database file.
    """
    def __init__(self, json_representation):
        self.filepath = json_representation["filename"]

    def connect(self):
        """Connect to the document.

        Returns
        -------
        ContextManager
            An `orm.Connection` context manager handling connection to the database file the document represents.
        
        Example
        -------
        To be used as a context manager, as follows:
        ```
        with doc.connect():
            db.select(...)
        ```
        """
        return Connection(self.filepath)

    def point(self, identifier):
        """Constructs a point from a vertex identifier.

        Parameters
        ----------
        identifier : int
            A vertex identifier for a vertex in the document.

        Returns
        -------
        Point
            An `img.Point` object representing the provided identifier.
        """
        return Point(self.filepath, identifier)

class Dataset:
    """A set of documents.

    Parameters
    ----------
    documents : Document list
        A list of all documents to be used in the data set.

    Attributes
    ----------
    documents : Document list
        A list of all documents in the data set.

    ground_truth : GroundTruth
        The points labeled "positive" in the data set.
    """
    def __init__(self, documents):
        self.documents = documents
        self._ground_truth = None

    @classmethod
    def load(cls, filepath):
        """Loads a data set from file.

        Parameters
        ----------
        filepath : str
            Filepath for JSONL representation of the data set.

        Returns
        -------
        Dataset
            `Dataset` object encoded in the JSONL file.
        """
        with open(filepath, "r") as f:
            docs = [Document(json.loads(line)) for line in f.readlines()]
        return cls(docs)

    @property
    def ground_truth(self):
        # cached construction
        if not self._ground_truth:
            points = []
            for document in self.documents:
                with document.connect():
                    points += positive_vertices()
            self._ground_truth = GroundTruth(points)
        return self._ground_truth

class GroundTruth:
    """Ground truth annotations from a set of documents.

    Parameters
    ----------
    points : img.Point list
        A list of points in the ground truth.

    Attributes
    ----------
    points : img.Point list
        A list of points in the ground truth.
    """
    def __init__(self, points):
        self.points = points
"""Document-level information and statistics."""

from img import Point
from orm import Connection, positive_vertices, all_vertices, db_session
from enum import Enum, auto
from difflib import get_close_matches
import json
from os import path

class Split(Enum):
    """Enumeration for labeling documents with their role in a data set split."""
    TRAIN = auto()
    TEST = auto()
    VALIDATE = auto()

_SPLIT_OPTIONS = {
    "train" : Split.TRAIN,
    "test" : Split.TEST,
    "validate" : Split.VALIDATE
}

def split_of_string(string):
    """Converts string to closest split option using difflib.

    Parameters
    ----------
    string : str
        String to be converted.

    Returns
    -------
    Split
        Enum value represented by provided string.
    """
    option = get_close_matches(string, _SPLIT_OPTIONS.keys(), 1)[0]
    return _SPLIT_OPTIONS[option]

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

    splits : Split list
        List of enum values specifying the split type of the document.

    domain : img.Point set
        Set of all points in the document.

    ground_truth : img.Point set
        Set of all points in the document labeled "positive" by the user.
    """
    def __init__(self, json_representation):
        self.filepath = json_representation["filename"]
        self.splits = [split_of_string(split) for split in json_representation["split"]]
        self._domain = None
        self._ground_truth = None

    def __str__(self):
        file_base = path.splitext(path.basename(self.filepath))[0]
        return f"<doc:{file_base}>"

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

    @property
    def domain(self):
        # cached domain construction
        if self._domain is None:
            with self.connect():
                with db_session:
                    self._domain = set( (self.point(vertex.id) for vertex in all_vertices()) )
        return self._domain

    @property
    def ground_truth(self):
        # cached ground truth construction
        if self._ground_truth is None:
            with self.connect():
                with db_session:
                    self._ground_truth = set( (self.point(vertex.id) for vertex in positive_vertices()) )
        return self._ground_truth

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
    """
    def __init__(self, documents):
        self.documents = documents
        self._ground_truth = None

    def documents_by_split(self, split):
        """Iterates over all documents matching the provided split type.

        Parameters
        ----------
        split : Split
            Split type to filter documents by.

        Yields
        ------
        Document
            Document object matching the provided split type.
        """
        for document in self.documents:
            if split in document.splits:
                yield document

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

    def domain(self, split=None):
        """All points in the documents in the data set.

        Parameters
        ----------
        split : Split, optional
            If provided, will provide the points *only* in the documents matching the split type.

        Returns
        -------
        img.Point list
            A list of points in the appropriate split.
        """
        if split is None:
            documents = self.documents
        else:
            documents = self.documents_by_split(split)
        output = set()
        for document in documents:
            output = output.union( document.domain )
        return output

    def ground_truth(self, split=None):
        """All points in the documents in the data set labeled "positive" by the user.

        Parameters
        ----------
        split : Split, optional
            If provided, will provide the points *only* in the documents matching the split type.

        Returns
        -------
        img.Point list
            A list of all positive points in the appropriate split.
        """
        if split is None:
            documents = self.documents
        else:
            documents = self.documents_by_split(split)
        output = set()
        for document in documents:
            output = output.union( document.ground_truth )
        return output

    def filter_points(self, points, split):
        """Removes points that don't come from a document from the right split.

        Parameters
        ----------
        points : img.Point list
            A list of points to be filtered.
        
        split : Split
            The split to filter by.

        Yield
        -------
        img.Point
            A point from the provided split.
        """

        split_map = {document.filepath : document.splits for document in self.documents}

        for point in points:
            point_splits = split_map[point.filepath]
            if split in split_map[point.filepath]:
                yield point
        
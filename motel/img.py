"""Defines sparse images - the result of evaluating motifs on documents.
"""

import orm, log, motifs
import json
from collections import defaultdict

logger = log.get("img")

class Point:
    """A node in a document, as selected by a motif.

    Parameters
    ----------
    filepath : str
        The filepath of the document the point is selected from.

    identifier : int
        The identifier for the point in the document at `filepath`.

    Attributes
    ----------
    filepath : str
        The filepath of the document the point is selected from.

    identifier : int
        The identifier for the point in the document at `filepath`.
    """
    def __init__(self, filepath, identifier):
        self.filepath = filepath
        self.identifier = identifier
    
    def __str__(self):
        return f"{self.identifier}"

    def to_json(self):
        """Converts point object to simple JSON representation.
        
        Returns
        -------
        dict
            A JSON-like representation of `self`.

        Notes
        -----
        Functional inverse of `Point.of_json` - that is, `p = Point.of_json(p.to_json())`.
        """
        return {
            "file" : self.filepath,
            "identifier" : self.identifier
        }

    def __eq__(self, other):
        return (self.filepath == other.filepath) and (self.identifier == other.identifier)
    
    @classmethod
    def of_json(cls, json_representation):
        """Constructs a point object from a JSON-like representation.

        Parameters
        ----------
        json_representation : dict
            A JSON-like representation of a point. Assumes existence of a "file" and "identifier" key.

        Returns
        -------
        Point
            A point object stored in the JSON representation.

        Notes
        -----
        Functional inverse of `to_json` - that is, `p = Point.of_json(p.to_json())`.
        """
        return cls(json_representation["file"], json_representation["identifier"])

    def __hash__(self):
        return hash( (self.filepath, self.identifier) )

class SparseImage:
    """The image of a set of motifs on a set of documents.

    Attributes
    ----------
    motifs : motifs.Motif list
        A set of `Motif` objects.

    rows : motifs.Motif -> Point list
        A dictionary mapping `Motif` objects to an image - a list of `Point` objects.

    domain : Point list
        A list of all points selected by motifs in the image.
    """
    def __init__(self):
        self.motifs = []
        self.rows = defaultdict(lambda: [])
        logger.info(f"Sparse image {self} created.")

    def register_motif(self, motif):
        """Registers a motif in the sparse image.

        Parameters
        ----------
        motif : motif.Motif
            A `Motif` object to register in the sparse image.

        Notes
        -----
        Modifies the `SparseImage` object in place.
        """
        self.motifs.append(motif)
    
    def register_motifs(self, *args):
        """Registers multiple motifs in the sparse image.

        Parameters
        ----------
        *args : motif.Motif list
            A list of `Motif` objects to register in the sparse image.

        Notes
        -----
        Modifies the `SparseImage` object in place.

        See Also
        --------
        `register_motif` - `register_motifs` relies on `register_motif` to process the parameters.
        """
        for motif in args:
            self.register_motif(motif)

    def evaluate_motifs(self, document):
        """Evaluate all registered motifs on a document.

        Parameters
        ----------
        document : doc.Document
            `doc.Document` object representing the doc-to-be-evaluated.

        Notes
        -----
        Modifies the `SparseImage` object in place.

        `evaluate_motifs` is *not* idempotent - evaluating the same document multiple times will duplicate the image.
        """
        with document.connect():
            for motif in self.motifs:
                logger.info(f"Evaluating motif {motif} on {document}...")
                # do the evaluation
                values = [document.point(id) for id in motif.evaluate()]
                self.rows[motif] += values
                logger.info(f"Motif {motif} finished evaluating on {document}. Selected {len(values)} vertices.")

    def dump(self, filepath):
        """Writes a sparse image to file.

        Parameters
        ----------
        filepath : str
            File path to write the sparse image to.

        See Also
        --------
        `load` - `dump` and `load` are functional inverses.
        """
        logger.info(f"Writing {self} to {filepath}...")
        lines = []
        for motif in self.motifs:
            entry = {
                    "motif" : motif.to_json(),
                    "image" : [point.to_json() for point in self.rows[motif]]
            }
            lines.append(f"{json.dumps(entry)}\n")
        with open(filepath, "w") as f:
            f.writelines(lines)
        logger.info(f"Image {self} written to {filepath}.")

    @classmethod
    def load(cls, filepath):
        """Loads a sparse image from file.

        Parameters
        ----------
        filepath : str
            File path to load the sparse image from.

        Returns
        -------
        SparseImage
            `SparseImage` object as represented by the file at `filepath`.

        See Also
        --------
        `dump` - `load` and `dump` are functional inverses.
        """
        logger.info(f"Loading sparse image from {filepath}...")
        image = cls()
        with open(filepath, "r") as f:
            entries = [json.loads(line) for line in f.readlines()]
        for entry in entries:
            motif = motifs.Motif(entry["motif"])
            image.register_motif(motif)
            points = [Point.of_json(json_rep) for json_rep in entry["image"]]
            image.rows[motif] += points
        logger.info(f"Image {image} loaded from {filepath}.")
        return image

    def motif_domain(self, motif):
        """Set of points a motif classifies.

        Parameters
        ----------
        motif : motifs.Motif
            `motif.Motif` object whose classification we care about.

        Returns
        -------
        Point list
            List of points classified by the provided motif.
        
        See Also
        --------
        `SparseImage.domain` - attribute providing the whole domain of an image.
        """
        return self.rows[motif]

    @property
    def domain(self):
        results = []
        for motif in self.motifs:
            results += self.motif_domain(motif)
        return results
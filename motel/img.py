import orm
import log
import json
from collections import defaultdict

logger = log.get("img")

class Point:
    def __init__(self, filepath, identifier):
        self._file = filepath
        self._identifier = identifier
    
    def __str__(self):
        return f"{self._identifier}"

    def to_json(self):
        return {
            "file" : self._file,
            "identifier" : self._identifier
        }
    
    @classmethod
    def of_json(cls, json_representation):
        return cls(json_representation["file"], json_representation["identifier"])

class SparseImage:
    def __init__(self):
        self.motifs = []
        self.rows = defaultdict(lambda: [])
        logger.info(f"Sparse image {self} created.")

    def register_motif(self, motif):
        self.motifs.append(motif)
        logger.info(f"Motif {motif} registered in image {self}.")
    
    def register_motifs(self, *motifs):
        for motif in motifs:
            self.register_motif(motif)

    def evaluate_motifs(self, filepath):
        with orm.Connection(filepath):
            for motif in self.motifs:
                logger.info(f"Evaluating motif {motif} on {filepath}...")
                # do the evaluation
                values = [Point(filepath, id) for id in motif.evaluate()]
                self.rows[motif] += values
                logger.info(f"Motif {motif} finished evaluating on {filepath}. Selected {len(values)} vertices.")

    def dump(self, filepath):
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
        logger.info(f"Loading sparse image from {filepath}...")
        image = cls()
        with open(filepath, "r") as f:
            entries = [json.loads(line) for line in f.readlines()]
        for entry in entries:
            motif = entry["motif"]
            image.register_motif(motif)
            points = [Point.of_json(json_rep) for json_rep in entry["image"]]
            image.rows[motif].append(points)
        logger.info(f"Image {image} loaded from {filepath}.")
        return image
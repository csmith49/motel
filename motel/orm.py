from pony.orm import *
from os import path
import log, settings

logger = log.get("orm")

db = Database()

# define the schema

# vertices represent the things we want to select
class Vertex(db.Entity):
    attributes = Set("Attribute")
    incoming = Set("Edge")
    outgoing = Set("Edge")
    label = Optional(str)

    @classmethod
    @db_session
    def make(cls, **kwargs):
        # construct the vertex and add all found attributes from kwargs
        vertex = cls()
        for key, item in kwargs.items():
            Attribute(kind=key, value=item, vertex=vertex)
        # commit the changes so we can pull out the primary key
        commit()
        logger.info(f"Constructed vertex {vertex.id}")
        return vertex.id

    @property
    def edges(self):
        yield from self.incoming
        yield from self.outgoing

    def to_json(self, avoid=None):
        attrs = dict(map(lambda a: a.tuple, self.attributes))
        if avoid is not None:
            attrs = {k : v for k, v in attrs.items() if k not in avoid}
        return {
            "identifier" : self.id,
            "label" : attrs
        }

    def neighbors(self, distance=1):
        for edge in self.incoming:
            if edge.weight <= distance:
                yield edge.source
                yield from edge.source.neighbors(distance=distance - edge.weight)
        for edge in self.outgoing:
            if edge.weight <= distance:
                yield edge.destination
                yield from edge.source.neighbors(distance=distance - edge.weight)

# attributes label vertices
class Attribute(db.Entity):
    kind = Required(str)
    value = Required(str)
    vertex = Required(Vertex)

    @property
    def tuple(self):
        return (self.kind, self.value)

# edges connect vertices
class Edge(db.Entity):
    kind = Required(str)
    source = Required(Vertex, reverse="outgoing")
    destination = Required(Vertex, reverse="incoming")

    @classmethod
    @db_session
    def make(cls, source_id, label, destination_id):
        source, destination = Vertex[source_id], Vertex[destination_id]
        edge = Edge(kind=label, source=source, destination=destination)
        commit()
        logger.info(f"Constructed edge {source_id} --{label}-> {destination_id}")
        return edge.id

    def to_json(self, avoid=None):
        edge = {
            "source" : self.source.id,
            "destination" : self.destination.id,
        }
        if avoid is None or (avoid is not None and self.kind not in avoid):
            edge["label"] = self.kind
        return edge

    @property
    def weight(self):
        try:
            return settings.EDGE_WEIGHTS[self.kind]
        except: pass
        try:
            return settings.EDGE_WEIGHTS[self.kind.split(":")[0]]
        except: pass
        return settings.EDGE_WEIGHT_DEFAULT

    @classmethod
    def between(cls, *vertices):
        yield from Edge.select(lambda e: e.source in vertices and e.destination in vertices)

# constructing neighborhoods
def neighborhood(origin, distance=1):
    """Finds the neighborhood graph around a single vertex.

    Parameters
    ----------
    origin : Vertex
        `Vertex` entity acting as the "center" of the neighborhood.

    distance : int, optional
        The maximum distance where `Vertex` entities can be considered neighbors.

    Returns
    -------
    Vertex list, Edge list
        Pair of `Vertex` and `Edge` entity lists describing the neighborhood graph.

    Notes
    -----
    Distance calculations are dependent on the edge weight parameters in `settings`.

    See Also
    --------
    `Vertex.neighbors` - computation of vertices close to the origin.

    `Edge.between` - computation of all edges between the neighborhood vertices.

    `Edge.weight` - determination of an edge weight, based on values in `settings`.

    """
    vertices = set(origin.neighbors(distance=distance))
    edges = set(Edge.between(*vertices))
    return vertices, edges

def positive_vertices():
    """All vertices labeled "positive" by the user.

    Yields
    ------
    Vertex
        A `Vertex` entity with the "positive" value for the "user:label" attribute.
    """
    for attr in Attribute.select(lambda a: a.kind == "user:label" and a.value == "positive"):
        yield attr.vertex

def all_vertices():
    """All vertices in the connected database.

    Yields
    ------
    Vertex
        A `Vertex` entity in the database.
    """
    for vertex in Vertex:
        yield vertex

# context manager for connecting to a database
class Connection:
    """Context manager for automatically opening and closing database connections.

    Parameters
    ----------
    filepath : str
        Filepath to the database-to-be-connected-to.

    Examples
    --------
    Intended for use as a context manager, as follows:
    ```
    with Connection(":memory:"):
        db.select(...)
    ```
    """
    def __init__(self, filepath):
        self._filepath = filepath
        self._db = Database()
    
    def __enter__(self):
        logger.info(f"Initiating connection to {self._filepath}...")
        self._db.bind(provider='sqlite', filename=path.abspath(self._filepath), create_db=True)
        self._db.generate_mapping(create_tables=True)
        logger.info(f"Connection to {self._filepath} established.")
        return self._db

    def __exit__(self, *args):
        logger.info(f"Releasing connection to {self._filepath}...")
        self._db.disconnect()
        logger.info(f"Connection to {self._filepath} released.")
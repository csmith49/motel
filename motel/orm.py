from pony.orm import *
from os import path
from pathlib import Path
import log, settings

logger = log.get("orm")

# registration decorator
def register(parent):
    def decorator(obj):
        name = obj.__name__
        setattr(parent, name, obj)
        return obj
    return decorator

# define the schema as a class that constructs the ORM on initialization - otherwise we can't get the mappings
class ORM:
    def __init__(self, db):
        self.db = db

        # vertices represent the things we want to select
        @register(self)
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
        @register(self)
        class Attribute(db.Entity):
            kind = Required(str)
            value = Required(str)
            vertex = Required(Vertex)

            @property
            def tuple(self):
                return (self.kind, self.value)

        # edges connect vertices
        @register(self)
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
        @register(self)
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

        @register(self)
        def positive_vertices():
            """All vertices labeled "positive" by the user.

            Yields
            ------
            Vertex
                A `Vertex` entity with the "positive" value for the "user:label" attribute.
            """
            for attr in Attribute.select(lambda a: a.kind == "user:label" and a.value == "positive"):
                yield attr.vertex

        @register(self)
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
    with Connection(":memory:") as orm:
        orm.db.select(...)
    ```
    """
    def __init__(self, filepath):
        self._filepath = filepath
        self._db = Database()
        self._orm = ORM(self._db)
    
    def __enter__(self):
        # generate the folder path if it isn't there
        Path(path.dirname(self._filepath)).mkdir(parents=True, exist_ok=True)
        # then continue with the regular connections
        logger.info(f"Initiating connection to {self._filepath}...")
        self._db.bind(provider='sqlite', filename=path.abspath(self._filepath), create_db=True)
        self._db.generate_mapping(create_tables=True)
        logger.info(f"Connection to {self._filepath} established.")
        return self._orm

    def __exit__(self, *args):
        logger.info(f"Releasing connection to {self._filepath}...")
        self._db.disconnect()
        logger.info(f"Connection to {self._filepath} released.")
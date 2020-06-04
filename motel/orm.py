from pony.orm import *
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

    @property
    def json(self):
        attrs = dict(map(lambda a: a.tuple, self.attributes))
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

    @property
    def json(self):
        return {
            "source" : self.source.id,
            "destination" : self.destination.id,
            "label" : self.kind
        }

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
    vertices = set(origin.neighbors(distance=distance))
    edges = set(Edge.between(*vertices))
    return vertices, edges

def positive_vertices():
    for attr in Attribute.select(lambda a: a.kind == "user:label" and a.value == "positive"):
        yield attr.vertex

from pony.orm import *
import log

logger = log.get("orm")

db = Database()

# define the schema

# vertices represent the things we want to select
class Vertex(db.Entity):
    value = Required(str)
    attributes = Set("Attribute")
    incoming = Set("Edge")
    outgoing = Set("Edge")
    label = Optional(str)

    @classmethod
    @db_session
    def make(cls, value, **kwargs):
        # construct the vertex and add all found attributes from kwargs
        vertex = cls(value=value)
        for key, item in kwargs.items():
            Attribute(kind=key, value=item, vertex=vertex)
        # commit the changes so we can pull out the primary key
        commit()
        logger.info(f"Constructed vertex {vertex.id} with value '{value}'")
        return vertex.id

class Attribute(db.Entity):
    kind = Required(str)
    value = Required(str)
    vertex = Required(Vertex)

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

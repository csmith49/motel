import orm
import json
from collections import defaultdict

# utilities for parsing json reps of vertices and edges
def parse_vertex(vertex):
    id = vertex['identifier']
    parameters = {}
    for label in vertex['label']:
        parameters[label['attribute']] = label['value']
    return id, parameters

def parse_edge(edge):
    source = vertex['source']
    destination = vertex['destination']
    label = vertex['label']['constant']
    return source, label, destination

# motif class - imported as a json rep from the ocaml synthesis tool
class Motif:
    # construction just takes edges and vertices
    def __init__(self, selector, vertices, edges):
        self.selector = selector
        self.vertices = vertices
        self.edges = edges
    
    # construction parses the json string and pulls out edges and vertices
    @classmethod
    def make(cls, str):
        # parse the json, and pull out the structure and selectors
        motif = json.loads(str)
        # vertices first
        vertices = {}
        for vertex in motif['structure']['vertices']:
            id, parameters = parse_vertex(vertex)
            vertices[id] = parameters
        # then edges, as a matrix
        edges = defaultdict(lambda: [])
        for edge in motif['structure']['edges']:
            source, label, destination = parse_edge(edge)
            edge[source].append( (label, destination) )
        return cls(selector=motif['selector'], edges=edges, vertices=vertices)
    
    # evaluation uses orm to find a vertices in the current db that match the motif
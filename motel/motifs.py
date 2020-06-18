import orm
import json

def to_sql(identifier):
    return f"_{identifier}"

class Predicate:
    def __init__(self, key, value):
        self.key = key
        self.value = value
    
    def __str__(self):
        return f"{self.key} = {self.value}"

    @property
    def subquery(self):
        return f'''SELECT vertex FROM Attribute WHERE kind = "{self.key}" AND value = "{self.value}"'''

    def to_pair(self):
        return self.key, self.value

class Filter:
    def __init__(self, json_representation):
        self.predicates = [Predicate(k, v) for (k, v) in json_representation.items()]

    def __str__(self):
        predicate_strings = map(lambda pred: str(pred), self.predicates)
        return f"[{' & '.join(predicate_strings)}]"

    @property
    def where_clause(self):
        result = "TRUE"
        for predicate in self.predicates:
            result = f"id in ({predicate.subquery}) AND {result}"
        return result

    @property
    def is_empty(self):
        return not self.predicates

    def to_json(self):
        return {k : v for k, v in map(lambda pred: pred.to_pair(), self.predicates)}

class Edge:
    def __init__(self, json_representation):
        self.source = json_representation["source"]
        self.destination = json_representation["destination"]
        self.label = json_representation["label"]
    
    def __str__(self):
        return f"{self.source} --[{self.label}]-> {self.destination}"

    @property
    def select_statement(self):
        return f'''SELECT source AS {to_sql(self.source)}, destination AS {to_sql(self.destination)} FROM Edge WHERE kind = "{self.label}"'''

    def to_json(self):
        return {
            "source" : self.source,
            "destination" : self.destination,
            "label" : self.label
        }

class Vertex:
    def __init__(self, json_representation):
        self.identifier = json_representation["identifier"]
        self.filter = Filter(json_representation["label"])

    def __str__(self):
        return f"{self.identifier} @ {self.filter}"

    @property
    def select_statement(self):
        if self.filter.is_empty:
            return f"SELECT id AS {to_sql(self.identifier)} FROM Vertex"
        else:
            return f"SELECT id AS {to_sql(self.identifier)} FROM Vertex WHERE {self.filter.where_clause}"

    def to_json(self):
        return {
            "identifier" : self.identifier,
            "label" : self.filter.to_json()
        }

class Motif:
    def __init__(self, json_representation):
        self.selector = json_representation["selector"]
        self.vertices = [Vertex(entry) for entry in json_representation["structure"]["vertices"]]
        self.edges = [Edge(entry) for entry in json_representation["structure"]["edges"]]

    @property
    def query(self):
        statements = map(lambda obj: f"({obj.select_statement})", self.vertices + self.edges)
        return f"SELECT DISTINCT {to_sql(self.selector)} FROM {' NATURAL JOIN '.join(statements)}"

    @classmethod
    def of_string(cls, string):
        return cls(json.loads(string))

    def to_json(self):
        return {
            "selector" : self.selector,
            "structure" : {
                "edges" : [edge.to_json() for edge in self.edges],
                "vertices" : [vertex.to_json() for vertex in self.vertices]
            }
        }

    # evaluates in the currently bound db
    def evaluate(self):
        with orm.db_session:
            return orm.db.select(self.query)
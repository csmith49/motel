"""Defines motifs and the relevant sub-objects.
"""

import orm
import json

def to_sql(identifier):
    """Converts an identifier to a SQL-friendly form.

    Parameters
    ----------
    identifier : int
        Vertex identifier to be converted.

    Returns
    -------
    str
        SQL-friendly string representing the provided indentifier.
    """
    return f"_{identifier}"

class Predicate:
    """Attribute-level requirement on a vertex.

    Parameters
    ----------
    key : str
        Name of attribute to be checked.

    value : str or int
        The value the provided attribute should have.

    Attributes
    ----------
    key : str
        Stores the provided attribute key.

    value : str or int
        Stores the provided attribute value.

    subquery : str
        Predicate represented as a SQL sub-query selecting all vertices satisfying the predicate.
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value
    
    def __str__(self):
        return f"{self.key} = {self.value}"

    @property
    def subquery(self):
        return f'''SELECT vertex FROM Attribute WHERE kind = "{self.key}" AND value = "{self.value}"'''

class Filter:
    """A collection of vertex-level predicates.

    Parameters
    ----------
    json_representation : dict
        JSON-like representation of the predicates involved in the filter.

    Attributes
    ----------
    predicates : Predicate list
        List of predicates the filter is comprised of.

    where_clause : str
        String representing the semantics of the filter as a SQL "where" clause.

    is_empty : bool
        Flag indicating whether or not the filter contains any predicates, or is trivially satisfiable.

    See Also
    --------
    `Predicate` - filters are comprised of `Predicate` objects.

    `Vertex` - every `Vertex` object is associated with a filter.
    """
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
        """Converts filter to a JSON-like representation.

        Returns
        -------
        dict
            A JSON-like representation of the filter.

        Notes
        -----
        Functional inverse of `Filter` construction.
        """
        return {k : v for k, v in map(lambda pred: (pred.key, pred.value), self.predicates)}

class Edge:
    """Directed, labeled connections between objects in a motif.

    Parameters
    ----------
    json_representation : dict
        JSON-like representation of the edge.

    Attributes
    ----------
    source : int
        Identifier for the source vertex of the edge.
    
    destination : int
        Identifier for the destination vertex of the edge.

    select_statement : str
        String representing the semantics of the edge as a SQL "select" statement.
    
    See Also
    --------
    `Motif` - motifs are comprised (in part) of `Edge` objects.
    """
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
        """JSON-like representation of an edge.

        Returns
        -------
        dict
            JSON-like representation of an edge.

        Notes
        -----
        Functional inverse with `Edge` construction.
        """
        return {
            "source" : self.source,
            "destination" : self.destination,
            "label" : self.label
        }

class Vertex:
    """Vertex in a motif.

    Parameters
    ----------
    json_representation : dict
        JSON-like representation for a vertex.

    Attributes
    ----------
    identifier : int
        Identifier for the vertex in the containing motif.
    
    filter : Filter
        Vertex-level requirements.

    select_statement : str
        String representing the semantics of the vertex as a SQL "select" query.

    See Also
    --------
    `Filter` - the `filter` attribute is a `Filter` object.

    `Motif` - motifs are comprised (in part) of `Vertex` objects.
    """
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
        """JSON-like representation of a vertex.

        Returns
        -------
        dict
            JSON-like representation of the vertex.

        Notes
        -----
        Functional inverse of `Vertex` construction.
        """
        return {
            "identifier" : self.identifier,
            "label" : self.filter.to_json()
        }

class Motif:
    """A pattern graph acting as a selector over documents.

    A motif is a graph - vertices represent objects in a document, and edges represent their relations. Vertices store attributes (including things like "text"), while edges carry a label and a direction specifying the relation between vertices.

    Parameters
    ----------
    json_representation : dict
        A JSON-like representation of a motif.

    Attributes
    ----------
    selector : int
        Identifier for the vertex representing the objects to be selected. Assume `selector in vertices`.

    vertices : Vertex list
        List of vertices contained in the motif.

    edges : Edge list
        List of edges contained in the motif.

    query : str
        String representing the semantics of the motif as a SQL query.
    
    See Also
    --------
    `Vertex` - objects stored in the `vertices` attribute.

    `Edge` - objects stored in the `edges` attribute.
    """
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
        """Constructs a motif from a string.

        Parameters
        ----------
        string : str
            String representation of a motif.

        Notes
        -----
        Assumes the string encodes a JSON-like object, as `of_string` just calls `json.loads`.
        """
        return cls(json.loads(string))

    def to_json(self):
        """Converts motif to a JSON-like representation.

        Returns
        -------
        dict
            JSON-like representation of the motif.

        Notes
        -----
        Inverse of `Motif` construction.
        """
        return {
            "selector" : self.selector,
            "structure" : {
                "edges" : [edge.to_json() for edge in self.edges],
                "vertices" : [vertex.to_json() for vertex in self.vertices]
            }
        }

    def evaluate(self, db):
        """Evaluates the motif in the currently-connected document.

        Paramters
        ---------
        Database
            A PonyORM database object currently bound.

        Returns
        -------
        int list
            List of identifiers from the currently-connected document selected by the motif.

        See Also
        `query` - `evaluate` constructs and evaluates the SQL query represented by the `query` attribute.
        """
        with orm.db_session:
            return db.select(self.query)
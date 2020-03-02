# get the local dependencies
import orm
import settings
# set up logging
import log
logger = log.get("nlp")
# load the nlp model
logger.info("Loading NLP model (en_core_web_sm)...")
import en_core_web_sm
nlp = en_core_web_sm.load()
logger.info("NLP model (en_core_web_sm) loaded.")
# any extra deps
import itertools

# extra pipeline steps determined by the settings
if settings.MERGE_ENTITIES:
    logger.info("NLP model will merge entities into a single token.")
    merge_entities = nlp.create_pipe("merge_entities")
    nlp.add_pipe(merge_entities)
if settings.MERGE_NOUN_CHUNKS:
    logger.info("NLP model will merge noun chunks into a single token.")
    merge_noun_chunks = nlp.create_pipe("merge_noun_chunks")
    nlp.add_pipe(merge_noun_chunks)

# add the id extension to track vertices from a token
from spacy.tokens import Token
Token.set_extension("id", default=None)

# utility for filtering out irrelevant tokens
def is_important(token):
    return not token.is_stop and not token.is_punct and not token.is_space

# convert the token to a dict for ease of manipulation
def convert(token):
    properties = {}
    # lemmatize the text
    value = token.lemma_
    # get the pos
    properties['pos'] = token.pos_
    # get the tag
    properties['tag'] = token.tag_
    # get any entity information
    if token.ent_type_:
        properties['entity'] = token.ent_type_
    # return the stripped representation
    return value, properties

# pairwise iteration (from itertools recipes @ https://docs.python.org/3.8/library/itertools.html)
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

# simple test
def process(str):
    # get the doc
    doc = nlp(str)
    # for chaining sentences together
    sentences = []
    # iterate over sentences
    for sentence in doc.sents:
        # contruct the node representing the sentence
        sentence_id = orm.Vertex.make("motel:sentence")
        sentences.append(sentence_id)
        # and record each token as we go
        tokens = []
        # first build our vertex representation of important tokens
        for token in sentence:
            if is_important(token):
                value, properties = convert(token)
                # generate a vertex for the token
                logger.info(f"Found token: \"{value}\" with properties: {properties}")
                vertex_id = orm.Vertex.make(value, **properties)
                # register the ID so we can make some edges
                token._.id = vertex_id
                tokens.append(vertex_id)
                # and make a containment edge
                orm.Edge.make(sentence_id, "motel:contains", vertex_id)
        # now build up the dependency tree across important tokens only
        for token in sentence:
            if is_important(token) and is_important(token.head) and token.dep_ != "ROOT":
                if settings.USE_VERBOSE_DEPENDENCIES:
                    label = "spacy:" + token.dep_
                else:
                    label = "spacy:dependency"
                logger.info(f"Found important dependency: {token._.id} - {label} - {token.head._.id}")
                edge_id = orm.Edge.make(token._.id, label, token.head._.id)
        # and add edges between important tokens representing order
        for tok1, tok2 in pairwise(tokens):
            orm.Edge.make(tok1, "motel:next", tok2)
    # add an edge between each sentence in sequence
    for sent1, sent2 in pairwise(sentences):
        orm.Edge.make(sent1, "motel:next", sent2)
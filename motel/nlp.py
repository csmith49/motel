# get the local dependencies
import settings
# set up logging
import log
logger = log.get("nlp")
# load the nlp model
logger.info("Loading NLP model (en_core_web_md)...")
import en_core_web_md
nlp = en_core_web_md.load()
logger.info("NLP model (en_core_web_md) loaded.")
# any extra deps
import itertools, re

# add the id extension to track vertices from a token
from spacy.tokens import Token
Token.set_extension("id", default=None)

# and the importance extension
def is_important(token):
    return not token.is_stop and not token.is_punct and not token.is_space
Token.set_extension("is_important", getter=is_important)

# extra pipeline steps determined by the settings
if settings.MERGE_ENTITIES:
    logger.info("NLP model will merge entities into a single token.")
    merge_entities = nlp.create_pipe("merge_entities")
    nlp.add_pipe(merge_entities)
if settings.MERGE_NOUN_CHUNKS:
    logger.info("NLP model will merge noun chunks into a single token.")
    merge_noun_chunks = nlp.create_pipe("merge_noun_chunks")
    nlp.add_pipe(merge_noun_chunks)

# pairwise iteration (from itertools recipes @ https://docs.python.org/3.8/library/itertools.html)
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

# TEXT-BASED LABEL MANAGEMENT

# extract labels from raw text representation
def text_labels(str):
    # the re we use to delimit positive examples
    pattern = re.compile(r"\[\[([^\[\]]*)\]\]")
    # grab the doc to use spacy's sentence parser
    doc = nlp(str)
    for sentence in doc.sents:
        # check if there's a positive label, and pull the text out
        matches = pattern.findall(sentence.text)
        # yield the text, or None - relies on assumption that there's only one label
        if len(matches) == 0:
            yield None
        elif len(matches) == 1:
            yield matches[0]
        else:
            logger.warning(f"More than one positive label found in: {sentence.text}")
            yield None

# remove any labels from the text
def remove_labels(str):
    return str.replace("[[", "").replace("]]", "")

# PROCESSING

# convert the token to a dict for ease of manipulation
def process_token(token):
    properties = {}
    # lemmatize the text
    value = token.lemma_
    # get the pos
    properties['spacy:pos'] = token.pos_
    # get the tag
    properties['spacy:tag'] = token.tag_
    # get any entity information
    if token.ent_type_:
        properties['spacy:entity'] = token.ent_type_
    # return the stripped representation
    return value, properties

# convert a sentence
def process_sentence(sentence, label, mapping):
    logger.info(f"Processing sentence: {sentence.text}")

    # construct node representing the sentence
    sentence_id = mapping.Vertex.make()

    # convert label to a spacy doc so we can compute cosine similarity
    labeled_token = None
    if label is not None:
        logger.info(f"Checking for positive label: {label}")
        label = nlp(label)
        # compute the token with the highest similarity, and record it
        similarity = float("-INF")
        for token in sentence:
            s = token.similarity(label)
            if s > similarity:
                labeled_token, similarity = token, s
        logger.info(f"Most similar token: {labeled_token.text}")
    else:
        logger.info("No positive label provided")

    # now process each token one by one
    tokens = []
    for token in sentence:
        # but only the important ones
        if is_important(token):
            value, properties = process_token(token)
            if token == labeled_token:
                properties["user:label"] = "positive"
            # generate the vertex
            logger.info(f"Found token: \"{value}\" with properties: {properties}")
            vertex_id = mapping.Vertex.make(text=value, **properties)
            # register the id so we can make some edges
            token._.id = vertex_id
            tokens.append(vertex_id)
            # and make the containment edge
            mapping.Edge.make(sentence_id, "motel:contains", vertex_id)
        else: pass

    # build up the dependency tree with another pass
    for token in sentence:
        if is_important(token) and is_important(token.head) and token.dep_ != "ROOT":
            if settings.USE_VERBOSE_DEPENDENCIES:
                label = "spacy:" + token.dep_
            else:
                label = "spacy:dependency"
            logger.info(f"Found important dependency: {token._.id} - {label} - {token.head._.id}")
            edge_id = mapping.Edge.make(token._.id, label, token.head._.id)

    # and then build up the edges between important tokens
    for token1, token2 in pairwise(tokens):
        mapping.Edge.make(token1, "motel:next", token2)

    # give back the sentence id for the higher-level process to handle
    return sentence_id

# simple test
def process(str, mapping):
    # get the labels in the text
    labels = text_labels(str)
    
    # strip labels and parse the doc
    doc = nlp(remove_labels(str))

    # process each sentence
    sentences = []
    for sentence, label in zip(doc.sents, labels):
        sentence_id = process_sentence(sentence, label, mapping)
        sentences.append(sentence_id)

    # chain the sentences together
    for sentence1, sentence2 in pairwise(sentences):
        mapping.Edge.make(sentence1, "motel:next", sentence2)
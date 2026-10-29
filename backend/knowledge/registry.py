"""Only entities belonging to the implemented runtime are registered."""
def load_entities():
    from knowledge.identity import entities as identity
    from knowledge.conversations import entities as conversations
    from knowledge.documents import entities as documents
    from knowledge.jobs import entities as jobs
    from knowledge.rag import entities as retrieval
    from knowledge.answers import entities as answers
    from knowledge.wiki import entities as wiki
    from knowledge.wiki import index_entities as wiki_index

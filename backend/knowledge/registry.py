"""Import only implemented capabilities into the application metadata."""

def load_entities():
    from .identity import entities as identity
    from .conversations import entities as conversations
    from .documents import entities as documents
    from .jobs import entities as jobs

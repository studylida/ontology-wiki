"""Run state vocabulary shared by persistence, execution and conversation writes."""
ACTIVE = frozenset({'accepted', 'retrieving', 'generating'})
TERMINAL = frozenset({'completed', 'cancelled', 'failed', 'interrupted'})
RETRYABLE = TERMINAL - {'completed'}

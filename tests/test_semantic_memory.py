from core import MemorySystem

def test_semantic_memory_retrieval():
    mem = MemorySystem()
    mem.add_semantic_fact('m1', 'Implemented login endpoint with JWT')
    mem.add_semantic_fact('m2', 'Fixed bug in payment processing')
    results = mem.semantic_search('login', limit=2)
    assert results
    assert any('login' in r.content.lower() for r in results)
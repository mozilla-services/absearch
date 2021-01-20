from absearch.counters import MemoryCohortCounters


def test_memory():
    counter = MemoryCohortCounters()

    for i in range(10):
        counter.incr('en-US', 'US', 'abc')
    counter.decr('en-US', 'US', 'abc')

    value = counter.get('en-US', 'US', 'abc')
    assert value == 9, value

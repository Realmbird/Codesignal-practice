# CodeSignal Practice — Task Manager

Practice problem modelled on the Constellation/Astra CodeSignal format.

## Format

- Six progressive levels, ~90 minutes total
- Implement `simulate(queries)` in `simulation.py`
- Each query is `[OPERATION, arg1, arg2, ...]`; return one result string per query
- Tests: `python -m unittest test_simulation.TestSimulate.test_level_1`
- No external libraries — stdlib only (`threading`, `asyncio`, `collections`, etc.)

## Levels

| Level | Topic | Time |
|-------|-------|------|
| 1 | ADD / GET / DELETE (dicts) | ~10 min |
| 2 | LIST / SEARCH / UPDATE (lists + sorting) | ~15 min |
| 3 | Priority + tags (sorting keys, sets) | ~20 min |
| 4 | Due dates + status (filtering, multi-sort) | ~15 min |
| 5 | Concurrent adds (`threading`) | ~10 min |
| 6 | Async batch fetch (`asyncio`) | ~10 min |

## Running tests

```bash
# single level
python -m unittest test_simulation.TestSimulate.test_level_1

# all levels
python -m unittest test_simulation
```

## Key hints from the email

- Read the tests — they are the spec. Ambiguity → trust the test.
- Don't worry about edge cases with no test coverage.
- Concurrency: use `threading.Lock` around shared mutable state.
- Async: `asyncio.gather` + `asyncio.run` is the pattern.
- IDs are auto-incremented integers starting at 1.

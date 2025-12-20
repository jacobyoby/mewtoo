# Test Suite

Comprehensive test suite for Mewtwo using pytest.

## Setup

Install test dependencies:

```bash
pip install -r requirements.txt
```

This will install pytest, pytest-cov, and pytest-mock.

## Running Tests

Run all tests:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_memory_reader.py
```

Run specific test:

```bash
pytest tests/test_memory_reader.py::TestMemoryReader::test_read_player_position
```

Run with coverage:

```bash
pytest --cov=. --cov-report=html
```

## Test Structure

- `tests/test_memory_reader.py` - Tests for memory reading functionality
- `tests/test_game_state.py` - Tests for game state management
- `tests/test_llm_optimizer.py` - Tests for LLM optimization components
- `tests/test_pokemon_agent.py` - Tests for the Pokemon agent (with mocks)
- `tests/conftest.py` - Pytest fixtures and configuration

## Test Coverage

The test suite covers:

- **Memory Reader**: All memory reading functions, error handling, edge cases
- **Game State**: Button presses, action execution, memory integration
- **LLM Optimizer**: Caching, prompt optimization, repetition detection
- **Pokemon Agent**: Action generation, step execution, state tracking

## Mocking

Tests use mocks for:
- PyBoy emulator (to avoid requiring ROM files)
- LLM providers (to avoid API calls)
- External dependencies

## Notes

- Tests are designed to run without requiring a ROM file
- Integration tests that require actual PyBoy/ROM should be marked with `@pytest.mark.integration`
- Run integration tests separately: `pytest -m integration`


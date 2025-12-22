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

### Unit Tests
- `tests/test_memory_reader.py` - Tests for memory reading functionality
- `tests/test_game_state.py` - Tests for game state management
- `tests/test_llm_optimizer.py` - Tests for LLM optimization components
- `tests/test_pokemon_agent.py` - Tests for the Pokemon agent (with mocks)
- `tests/test_metrics.py` - Tests for metrics tracking system

### Integration Tests
- `tests/test_metrics_integration.py` - Integration tests for metrics system

### Performance Tests
- `tests/test_performance.py` - Performance benchmarks and regression tests
  - Step time benchmarks (<50ms target)
  - Cache hit rate benchmarks (>80% target)
  - LLM latency benchmarks (<500ms target)
  - OCR timing benchmarks
  - Performance regression detection

### End-to-End Tests
- `tests/test_end_to_end.py` - Complete gameplay sequence tests
  - Early game sequence (start game -> get starter -> reach first town)
  - Menu navigation tests
  - Overworld movement tests
  - Dialogue handling tests
  - State transition tests

### Stress Tests
- `tests/test_stress.py` - Extended run and resource limit tests
  - 1000+ step runs
  - 5000+ step runs
  - Memory leak detection
  - Long-running stability tests
  - Cache size limit tests
  - Action history limit tests

### Edge Case Tests
- `tests/test_edge_cases.py` - Error recovery and stuck detection tests
  - LLM provider error recovery
  - Game state error recovery
  - Memory reading error recovery
  - Repetitive action detection
  - Position stuck detection
  - Same state persistence detection
  - Empty/long screen text handling
  - Rapid state changes
  - Invalid action handling

### Configuration
- `tests/conftest.py` - Pytest fixtures and configuration

## Test Coverage

The test suite covers:

- **Memory Reader**: All memory reading functions, error handling, edge cases
- **Game State**: Button presses, action execution, memory integration
- **LLM Optimizer**: Caching, prompt optimization, repetition detection
- **Pokemon Agent**: Action generation, step execution, state tracking
- **Metrics**: Performance metrics, cache statistics, LLM call tracking
- **Performance**: Benchmarks, regression tests, overhead measurement
- **End-to-End**: Complete gameplay sequences, menu navigation, movement
- **Stress**: Extended runs (1000+ steps), memory leak detection, stability
- **Edge Cases**: Error recovery, stuck detection, invalid inputs

## Running Specific Test Types

Run only unit tests:
```bash
pytest -m unit
```

Run only integration tests:
```bash
pytest -m integration
```

Run performance benchmarks:
```bash
pytest -m performance
```

Run end-to-end tests:
```bash
pytest -m e2e
```

Run stress tests:
```bash
pytest -m stress
```

Run edge case tests:
```bash
pytest -m edge_case
```

Skip slow tests:
```bash
pytest -m "not slow"
```

Run all tests except slow ones:
```bash
pytest -m "not slow"
```

## Mocking

Tests use mocks for:
- PyBoy emulator (to avoid requiring ROM files)
- LLM providers (to avoid API calls)
- External dependencies

## Notes

- Tests are designed to run without requiring a ROM file
- Integration tests that require actual PyBoy/ROM should be marked with `@pytest.mark.integration`
- Run integration tests separately: `pytest -m integration`


# PyCraft 2D - Test Suite

This directory contains a comprehensive unit test suite for the PyCraft 2D game. The tests are designed to validate all major game components and ensure code quality and reliability.

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_config.py             # Test configuration and utilities
├── simple_runner.py           # Simple test runner (no external deps)
├── run_tests.py              # Advanced test runner with coverage
├── test_requirements.txt      # Optional testing dependencies
├── core/                     # Core game logic tests
│   ├── __init__.py
│   └── test_game.py          # Main game class tests
├── entities/                 # Entity system tests
│   ├── __init__.py
│   └── test_entities.py      # Player, mobs, items tests
├── systems/                  # Game systems tests
│   ├── __init__.py
│   └── test_systems.py       # World, rendering, input tests
├── ui/                       # User interface tests
│   ├── __init__.py
│   └── test_ui.py            # Inventory, menus, HUD tests
├── utils/                    # Utility function tests
│   ├── __init__.py
│   └── test_utils.py         # Logger, performance, audio tests
├── world/                    # World system tests
│   ├── __init__.py
│   └── test_world.py         # Map, chunks, generation tests
└── integration/              # Integration tests
    ├── __init__.py
    └── test_integration.py   # Full system integration tests
```

## 🚀 Running Tests

### Quick Start (No Additional Dependencies)

```bash
# Navigate to the game directory
cd "d:\Projets\pygameTFE\pycraft game"

# Run all tests using the simple runner
python tests\simple_runner.py

# Run tests for a specific module
python tests\simple_runner.py core.test_game
```

### Advanced Testing (With Coverage)

```bash
# Install testing dependencies
pip install -r tests\test_requirements.txt

# Run with coverage reporting
python tests\run_tests.py --coverage

# Or using pytest (if installed)
pytest tests\ --cov=game --cov-report=html
```

### Individual Test Categories

```bash
# Run specific test categories
python -m unittest tests.core.test_game
python -m unittest tests.entities.test_entities
python -m unittest tests.systems.test_systems
python -m unittest tests.ui.test_ui
python -m unittest tests.utils.test_utils
python -m unittest tests.world.test_world
python -m unittest tests.integration.test_integration
```

## 📋 Test Categories

### Core Tests (`tests/core/`)
- **Game Class**: Main game initialization, state management, resource access
- **Game State**: Pause/resume, inventory state, time management
- **Resource Access**: Fonts, images, audio, data validation

### Entity Tests (`tests/entities/`)
- **Player**: Movement, health, harvesting, combat mechanics
- **Floating Items**: Item creation, pickup mechanics
- **Projectiles**: Arrow physics, damage calculation
- **Mobs**: AI behavior, health system, combat
- **Interactions**: Player-item, player-mob, collision detection

### System Tests (`tests/systems/`)
- **World Manager**: Chunk loading, tile management, mob spawning
- **Game State Manager**: Save/load, day/night cycle, item management
- **Render Manager**: Screen coordinates, visibility, rendering order
- **Input Manager**: Key mapping, mouse input, validation
- **Camera**: Following player, world-to-screen conversion
- **Chunk Manager**: Chunk generation, loading/unloading, memory management

### UI Tests (`tests/ui/`)
- **Inventory**: Item management, drag & drop, stack handling
- **Hotbar**: Slot selection, item placement, scrolling
- **Lifebar**: Health display, damage visualization
- **Menu**: Navigation, option selection
- **Input Box**: Text input, validation, character limits

### Utility Tests (`tests/utils/`)
- **Logger**: Log levels, formatting, file operations
- **Performance Monitor**: FPS calculation, memory tracking, thresholds
- **Audio Utils**: Sound loading, volume control, positional audio
- **Math Utils**: Vector operations, distance calculations, coordinates
- **Data Validation**: Input validation, sanitization, error handling

### World Tests (`tests/world/`)
- **Map**: Save data parsing, world initialization
- **Ground**: Tile creation, collision properties
- **Layer1 Objects**: Buildings, destructible objects, containers
- **Chunk System**: Coordinate calculations, naming, loading areas
- **World Generation**: Noise generation, biome selection, structure placement

### Integration Tests (`tests/integration/`)
- **Game Initialization**: Full startup sequence testing
- **Player-World Interaction**: Movement, chunk loading, item pickup
- **Inventory System**: Complete item management workflow
- **Save/Load System**: Data persistence, format compatibility
- **Performance Integration**: Sprite groups, memory management under load

## 🎯 Test Coverage

The test suite aims for comprehensive coverage of:

- ✅ **Core Game Logic** - Game initialization, state management
- ✅ **Entity Systems** - Player, mobs, items, interactions
- ✅ **World Management** - Chunks, tiles, generation
- ✅ **User Interface** - Menus, inventory, HUD components
- ✅ **Utility Functions** - Logging, performance, audio
- ✅ **Integration Points** - System interactions, data flow

## 🔧 Test Configuration

### MockGame Class
The test suite includes a `MockGame` class that provides:
- Mock sprite groups
- Mock resource managers
- Mock game state variables
- Safe testing environment without full game initialization

### BaseTestCase Class
All tests inherit from `BaseTestCase` which provides:
- Pygame initialization for testing
- Common test fixtures
- Cleanup procedures
- Mock game instances

## 📊 Test Reports

### Simple Runner Output
- Test execution summary
- Pass/fail counts
- Execution time
- Failed test details

### Advanced Runner Output (with coverage)
- All simple runner features
- Code coverage percentages
- HTML coverage reports
- Performance metrics

## 🛠️ Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure
```python
import unittest
from tests.test_config import BaseTestCase

class TestNewFeature(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Setup test fixtures
    
    def test_feature_functionality(self):
        # Arrange
        # Act
        # Assert
        pass
    
    def tearDown(self):
        super().tearDown()
        # Cleanup
```

### Best Practices
1. **Isolation**: Each test should be independent
2. **Mocking**: Use mocks for external dependencies
3. **Clear Names**: Test names should describe what they test
4. **Documentation**: Include docstrings explaining test purpose
5. **Edge Cases**: Test boundary conditions and error cases

## 🐛 Debugging Tests

### Running Single Tests
```bash
python -m unittest tests.core.test_game.TestGame.test_game_initialization -v
```

### Debugging with Print Statements
Tests inherit from `BaseTestCase` which sets up pygame safely for debugging.

### Common Issues
- **Pygame Initialization**: Tests handle pygame init/quit automatically
- **Import Errors**: Ensure the game directory is in the Python path
- **Mock Setup**: Verify all required attributes are mocked properly

## 📈 Continuous Integration

The test suite is designed to work in CI environments:
- No GUI dependencies (pygame HIDDEN mode)
- Comprehensive exit codes
- Machine-readable output options
- Minimal external dependencies for basic testing

## 🤝 Contributing

When adding new features to the game:
1. Write tests for new functionality
2. Update existing tests if interfaces change
3. Ensure all tests pass before committing
4. Maintain test coverage above 80%

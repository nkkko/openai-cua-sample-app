# OpenAI CUA Sample App - Developer Guide

## Core Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run CUA with local browser
python cli.py --computer local-playwright

# Run with Docker
python cli.py --show --computer docker

# Run examples
python -m examples.weather_example
python simple_cua_loop.py
```

## Code Style Guidelines
- **Imports**: stdlib first, third-party next, local modules last
- **Types**: Use Python type hints (Protocol, Literal, List, Dict)
- **Naming**: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_CASE
- **Error handling**: Explicit error raising with descriptive messages
- **Indentation**: 4 spaces
- **Documentation**: Docstrings for classes and public methods

## Project Architecture
- `agent/` - Agent implementation for CUA
- `computers/` - Implementations for different computer environments (local-playwright, docker)
- `examples/` - Sample usage examples
- `Computer` (Protocol) defines the interface for all computer environments

## Safety Considerations
- Domain blocking for browser environments
- Safety check callbacks for potentially unsafe operations
# Agent Guidelines for IPX800 v3 to MQTT Bridge

## Project Standards

### Language Requirements

**ALL content MUST be in English.** This includes:
- Code comments and docstrings
- Documentation (README, docs, etc.)
- Commit messages
- Variable and function names
- Log messages
- Test descriptions
- Configuration examples

**No French (or other languages) allowed in:**
- Source code
- Documentation
- Comments
- Variable names
- Any project files

### Code Standards

#### Python Style
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use double quotes for strings

#### Documentation
- All public functions must have docstrings
- Use Google-style docstrings
- Keep README.md updated with any new features

#### Testing
- All new features must have tests
- Maintain >80% code coverage
- Use pytest for testing
- Test names should be descriptive

#### Async Patterns
- Use `asyncio` properly
- Never block the event loop
- Use `asyncio.to_thread()` for synchronous operations
- Handle exceptions in async contexts

### Commit Message Convention

Use conventional commits:
```
feat: add new feature
fix: fix a bug
docs: update documentation
test: add or update tests
refactor: code refactoring
chore: maintenance tasks
```

### Project Structure

```
src/
├── __init__.py
├── main.py              # Entry point
├── config.py            # Configuration
├── state_manager.py     # State management
├── ipx800_client.py     # IPX800 API client
├── mqtt_client.py       # MQTT client
├── http_server.py       # HTTP server
└── auto_discovery.py    # HomeAssistant discovery

tests/
├── test_*.py            # Test files matching src modules
└── __init__.py
```

### MQTT Topic Standards

- Use configurable prefix (default: `ipx800`)
- Format: `{prefix}/{mac}/{entity_type}/{index}/{attribute}`
- Entities: relay, input
- Attributes: state, set (for commands)

### Environment Variables

All configuration must be via environment variables with `MQTT_TOPIC_PREFIX` pattern:
- Uppercase with underscores
- No default secrets
- Document all variables in README.md

## Review Checklist

Before completing any task:
- [ ] All code comments are in English
- [ ] All documentation is in English
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Type hints are present
- [ ] No French words in code or docs
- [ ] README.md is updated if needed
- [ ] Commit message follows convention

## Examples

### Good (English)
```python
async def update_relay_state(self, index: int, state: bool) -> None:
    """Update relay state and publish to MQTT.
    
    Args:
        index: Relay index (0-31)
        state: True for ON, False for OFF
    """
    logger.info("updating_relay_state", index=index, state=state)
```

### Bad (French)
```python
async def update_relay_state(self, index: int, state: bool) -> None:
    """Met à jour l'état du relais et publie sur MQTT.
    
    Args:
        index: Index du relais (0-31)
        state: True pour ON, False pour OFF
    """
    logger.info("mise_a_jour_etat_relais", index=index, state=state)
```

# Cactus AI Auto Trader - Best Practices

## Project Principles

1. **Modular Architecture**: Separate data ingestion, strategy logic, and execution
2. **Async First**: Use async/await for all I/O operations (exchange APIs, databases)
3. **Error Resilience**: Handle network failures, rate limits, and API errors gracefully
4. **Type Safety**: Use Python type hints throughout
5. **Testing**: Write tests alongside implementation (TDD where possible)
6. **Documentation**: Docstrings for all public functions and classes
7. **Configuration**: Environment-based config, never hardcode secrets

## Code Style

- Follow PEP 8 style guidelines
- Use Black formatter (line length 88)
- Use isort for import ordering
- Use mypy for type checking

## Commit Guidelines

- Small, focused commits
- Write clear commit messages (imperative mood)
- Commit frequently, don't batch changes
- Each commit should pass tests

## Project Structure

```
cactus/
├── app/                    # Main application code
│   ├── core/              # Core components
│   ├── exchanges/         # Exchange integrations
│   ├── strategies/        # Trading strategies
│   ├── data/              # Data pipeline
│   ├── risk/              # Risk management
│   ├── api/               # FastAPI endpoints
│   └── db/                # Database models
├── tests/                 # Test suite
├── config/                # Configuration files
└── scripts/               # Utility scripts
```

## Testing Strategy

- Unit tests for individual components
- Integration tests for data flow
- Mock exchange APIs in tests
- Aim for 80%+ code coverage

## Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Implement rate limiting
- Validate all external inputs
- Use connection pooling with limits

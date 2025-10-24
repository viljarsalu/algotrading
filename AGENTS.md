<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Build, Lint, and Test

- **Install/Update Dependencies:** `poetry install`
- **Run Linters & Formatters:**
  - `poetry run black .`
  - `poetry run isort .`
  - `poetry run flake8`
- **Run Type Checker:** `poetry run mypy .`
- **Run Tests:**
  - All tests: `poetry run pytest`
  - Single test file: `poetry run pytest tests/test_file.py`
  - Single test function: `poetry run pytest tests/test_file.py::test_function`

## Code Style Guidelines

- **Formatting:** Follow `black` with a line length of 88 characters.
- **Imports:** Use `isort` with the `black` profile. Imports should be grouped into standard library, third-party, and application-specific.
- **Types:** Use type hints for all function signatures. `mypy` is used for static type checking.
- **Naming:**
  - Classes: `PascalCase`
  - Functions/Variables: `snake_case`
  - Private methods/attributes: `_leading_underscore`
- **Error Handling:** Use `try...except` blocks for operations that can fail. Log errors and return a dictionary with `{'success': False, 'error': '...'}`.
- **Docstrings:** Provide clear docstrings for all public modules, classes, and functions.

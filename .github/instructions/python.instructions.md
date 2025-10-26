---
applyTo: '**/*.py'
---

# Python Coding Guidelines

These rules combine forevd conventions with widely accepted Python practices. Where industry defaults differ, follow the repo-specific rule noted here.

They intentionally mirror the upstream Firestone project so moving changes between repositories stays predictable; if you spot a divergence, flag it so we can reconcile both sides.

## Runtime & Dependencies
- Target Python **3.9+** as defined in `pyproject.toml`; keep code compatible with the supported range (even if newer features are tempting).
- Manage dependencies through Poetry and keep `pyproject.toml` and `poetry.lock` in sync when adding or bumping packages.

## Type Hints & Docstrings
- Annotate every function and method (including inner helpers) with precise parameter and return types.
- Prefer modern `typing` / `collections.abc` generics (`Iterator`, `Mapping`, `Sequence`, etc.) in annotations.
- Keep docstrings concise one-liners or short paragraphs consistent with existing modules; use reST-style sections only when they add value.

## Imports & Structure
- Use absolute imports; keep them grouped stdlib → third-party → local, separated by blank lines.
- Follow existing patterns (`os`, `io`, etc.) for filesystem helpers unless there is a clear benefit to switching to `pathlib.Path`.
- Keep module-level constants in uppercase with clear names.

## Coding Style
- Format with Black (100-character line length, already configured).
- Obey the pylint settings in `pyproject.toml`; choose descriptive identifiers within those constraints.
- Use f-strings, `Enum`/`Literal` where they clarify intent, and explicit encodings when touching files.
- Favor context managers for I/O and structured error handling (catch specific exceptions only when you can recover).

## Testing
- Place tests under `test/` and write them using pytest idioms (`assert`, fixtures, parametrization). Migrating legacy unittest code to pytest is encouraged when you touch it.
- Include or update tests for any behavioral change and keep them deterministic (use mocks, temp dirs, or fixtures as needed).
- Validate locally with `poetry run pytest`.

## Error Handling & Logging
- Raise specific exceptions with actionable messages.
- Log through `logging.getLogger(__name__)` (existing `_LOGGER` pattern) and keep messages concise but informative.

## Security & Robustness
- Avoid executing untrusted input and double-check file paths or templates before use.
- Preserve json/yaml loading safeguards already present in the repo (for example, `safe_load`).

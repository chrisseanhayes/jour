# Testing Jour

Jour's test suite runs inside Podman containers to guarantee complete environment isolation and prevent local host pollution.

Application logic, command handlers, and storage layers are tested through native Python unit tests using injected dependencies ([`AppFactory`](../jour_cli/app_factory.py) and [`Dependencies`](../jour_cli/shared/dependencies.py)). End-to-end binary installation and execution are validated via container smoke tests.

---

## Running Tests

### 1. Full Test Suite (Unit Tests + Container Smoke Tests)

To build the test image and execute both the unit test suite and smoke tests:

```bash
./podman-test.sh
```

This runs:
* All unit tests (`python3 -m unittest discover -s tests -p 'test_*.py'`)
* Container smoke tests (`sh tests/smoke.sh`)

---

### 2. Fast Unit Tests (Active Development)

During development, mount the repository volume into the container to run unit tests without rebuilding the container image:

```bash
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest discover -s tests -p 'test_*.py'
```

---

### 3. Run Specific Test Modules

Run individual test files directly:

```bash
# Cat command tests
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests/test_cat.py

# Delete command tests
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests/test_delete.py

# Tag indexing and query tests
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests/test_tags.py

# History logging and limit tests
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests/test_history.py

# Note input and editor resolution tests
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests/test_note_input.py
```

---

### 4. Run an Individual Test Method

To execute a single test method:

```bash
podman run --rm -v "$PWD:/app:ro" jour-cli-test python3 -m unittest tests.test_cat.CatNoteTests.test_cat_existing_note_writes_content_to_stdout
```

---

### 5. Run Container Smoke Tests Only

To test packaging, PATH availability, and end-to-end shell command execution:

```bash
podman run --rm jour-cli-test sh tests/smoke.sh
```

---

## Test Conventions

* **Naming**: Name all unit test files matching `test_*.py` so that `unittest discover` finds them automatically.
* **Isolation**: Use `Dependencies` or mock `NoteStore` / in-memory SQLite rather than touching host filesystem paths.
* **Output & Exit**: Assert against `dependencies.write_stdout`, `dependencies.write_stderr`, and `dependencies.exit` rather than raw `sys.stdout` or `sys.exit`.

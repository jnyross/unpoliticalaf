# Contributing

Follow the working agreement in [AGENTS.md](AGENTS.md).

## Test naming and discovery

- Put Python unit tests in `tests/` and name each test module
  `test_<subject>.py`, for example `tests/test_builder.py`.
- Use `unittest.TestCase` classes and name test methods `test_<behavior>`.
- Keep support modules and fixtures separate from test modules; do not give
  non-test Python files the `test_` prefix.

`make test` explicitly discovers `test_*.py` files in `tests/`. Other filename
styles, such as `builder_test.py` or `testbuilder.py`, are not collected, so new
tests must use the documented prefix and underscore.

## Running checks

Run `make setup` once to create the virtual environment. Run `make build` before
`make test`, because some tests inspect the generated site. Use `make verify` to
build the site, check its figures and pages, and run the tests together.

Pull requests run `make verify` in the Build and check workflow, so local and CI
test discovery use the same explicit filename pattern.

# Functional tests

Functional tests aims at testing each module as a whole.
They make sure the module parses given parameters into correct API calls.

Specific functions of modules should be tested in Unit tests.

## Running tests

```bash
pytest tests/functional
```

## Adding new tests

Every module tested should consist (at least) of the following cases:

- test_module_fails_on_wrong_parameters
- test_NAME_create_name
- test_NAME_create_without_display_name
- test_NAME_create_exception
- test_NAME_create_op_fails
- test_NAME_create_op_exception
- test_NAME_update
- test_NAME_update_exception
- test_NAME_update_op_fails
- test_NAME_update_op_exception
- test_NAME_present_not_changed
- test_NAME_absent_not_changed
- test_NAME_delete
- test_NAME_delete_exception
- test_NAME_delete_op_fails
- test_NAME_delete_op_exception

See already existing tests (e.g. `test_fusion_region.py`) for inspiration.

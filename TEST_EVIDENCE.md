# mcp2lint Test and Build Evidence

## Build Output
Built with `python -m build` against Python 3.11.2 environment:
- `dist/mcp2lint-0.1.0-py3-none-any.whl` (9,654 bytes)
- `dist/mcp2lint-0.1.0.tar.gz` (11,224 bytes)

## Isolated venv Installation & CLI Smoke Test
```console
$ python3 -m venv /tmp/mcp2lint-test-venv
$ /tmp/mcp2lint-test-venv/bin/pip install dist/mcp2lint-0.1.0-py3-none-any.whl
$ /tmp/mcp2lint-test-venv/bin/mcp2lint --version
mcp2lint 0.1.0
```

## Unit Test Suite (12 / 12 passed)
```console
$ pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-9.2.0, pluggy-1.7.0 -- /home/fish/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/fish/projects/mcp2lint
configfile: pyproject.toml
collecting ... collected 12 items

tests/test_scan.py::test_detects_renamed_fastmcp_import PASSED           [  8%]
tests/test_scan.py::test_detects_camel_case_attribute PASSED             [ 16%]
tests/test_scan.py::test_detects_transport_kwargs_on_constructor PASSED  [ 25%]
tests/test_scan.py::test_detects_removed_type_and_error PASSED           [ 33%]
tests/test_scan.py::test_clean_v2_file_reports_nothing PASSED            [ 41%]
tests/test_scan.py::test_syntax_error_is_skipped PASSED                  [ 50%]
tests/test_scan.py::test_scan_paths_walks_a_tree PASSED                  [ 58%]
tests/test_scan.py::test_skips_virtualenv_directories PASSED             [ 66%]
tests/test_scan.py::test_v2_streamable_http_client_is_not_flagged PASSED [ 75%]
tests/test_scan.py::test_removed_name_in_a_live_module_is_flagged PASSED [ 83%]
tests/test_scan.py::test_other_names_in_shared_context_are_not_flagged PASSED [ 91%]
tests/test_scan.py::test_request_context_is_flagged_wherever_it_is_imported PASSED [100%]

============================== 12 passed in 0.01s ==============================
```

## Real World Repositories Verification
Scanned against 3 open-source MCP repositories reporting MCP SDK v2 ModuleNotFoundError:
1. `gammaremover/gamma-watermark-remover-mcp`: 5 errors detected (2x MCP001, 3x MCP030)
2. `jelmervdm/sophos-firewall-mcp`: 3 errors detected (3x MCP001)
3. `zvec-ai/zvec-mcp-server`: 1 error detected (1x MCP001)

Official SDK v2 validation:
- `modelcontextprotocol/python-sdk` (v2 source): 0 findings (0 false positives).

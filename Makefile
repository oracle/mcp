SUBDIRS := $(filter-out src/dbtools-mcp-server src/mysql-mcp-server src/oci-pricing-mcp-server,$(wildcard src/*))

.PHONY: test format

build:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Building $$dir"; \
			name=$$(uv run tomlq -r '.project.name' $$dir/pyproject.toml); \
			version=$$(uv run tomlq -r '.project.version' $$dir/pyproject.toml); \
			if [ -d $$dir/oracle/*_mcp_server ]; then \
				init_py_file=$$(echo $$dir/oracle/*_mcp_server/__init__.py); \
				echo "\"\"\"\nCopyright (c) 2025, Oracle and/or its affiliates.\nLicensed under the Universal Permissive License v1.0 as shown at\nhttps://oss.oracle.com/licenses/upl.\n\"\"\"\n" > $$init_py_file; \
				echo "__project__ = \"$$name\"" >> $$init_py_file; \
				echo "__version__ = \"$$version\"" >> $$init_py_file; \
			fi; \
			cd $$dir && uv build && cd ../..; \
		fi \
	done

install:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Installing $$dir"; \
			cd $$dir && uv pip install . && cd ../..; \
		fi \
	done

sync:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Installing $$dir"; \
			cd $$dir && uv sync --locked --all-extras --dev && cd ../..; \
		fi \
	done

lock:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Installing $$dir"; \
			cd $$dir && uv lock && cd ../..; \
		fi \
	done

test:
	uv tool run --from 'tox==4.30.2' tox -e lint
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Testing $$dir"; \
			cd $$dir && uv run pytest && cd ../..; \
		fi \
	done

format:
	uv tool run --from 'tox==4.30.2' tox -e format

e2e-tests: build install
	behave tests/e2e/features && cd ..

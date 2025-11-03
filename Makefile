SUBDIRS := $(filter-out src/dbtools-mcp-server src/mysql-mcp-server src/oci-pricing-mcp-server src/oracle-db-doc-mcp-server,$(wildcard src/*))

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

lint:
	uv tool run --from 'tox==4.30.2' tox -e lint

test:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Testing $$dir"; \
			cd $$dir && \
				COVERAGE_FILE=../../.coverage.$$(_basename=$$(basename $$dir); echo $$_basename) \
				uv run pytest --cov=. --cov-branch --cov-append --cov-report=html --cov-report=term-missing && \
			cd ../..; \
		fi \
	done
	$(MAKE) combine-coverage

combine-coverage:
	uv run coverage combine
	uv run coverage html
	uv run coverage report --fail-under=69

format:
	uv tool run --from 'tox==4.30.2' tox -e format

e2e-tests: build install
	behave tests/e2e/features && cd ..

SUBDIRS ?= $(filter-out src/dbtools-mcp-server src/mysql-mcp-server src/oci-pricing-mcp-server src/oracle-db-doc-mcp-server src/oracle-db-mcp-java-toolkit,$(wildcard src/*))

.PHONY: test format

build:
	@set -e -o pipefail; \
	for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Building $$dir"; \
			name=$$(python -c "import tomllib; print(tomllib.load(open('$$dir/pyproject.toml', 'rb'))['project']['name'])"); \
			version=$$(python -c "import tomllib; print(tomllib.load(open('$$dir/pyproject.toml', 'rb'))['project']['version'])"); \
			if [ -d $$dir/oracle/*_mcp_server ]; then \
				init_py_file=$$(echo $$dir/oracle/*_mcp_server/__init__.py); \
				printf '"""\nCopyright (c) 2025, Oracle and/or its affiliates.\nLicensed under the Universal Permissive License v1.0 as shown at\nhttps://oss.oracle.com/licenses/upl.\n"""\n\n' > $$init_py_file; \
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

lock-check:
	@for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Installing $$dir"; \
			cd $$dir && uv lock --check && cd ../..; \
		fi \
	done

lint:
	uv tool run ruff check

test:
	@set -e -o pipefail; \
	for dir in $(SUBDIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Testing $$dir"; \
			( cd $$dir && \
				COVERAGE_FILE=../../.coverage.$$(basename $$dir) \
				uv run pytest --cov=. --cov-branch --cov-append --cov-report=html --cov-report=term-missing ) || exit 1; \
		fi \
	done
	$(MAKE) combine-coverage

combine-coverage:
	uv run coverage combine
	uv run coverage html
	uv run coverage report --fail-under=69

test-publish:
	@set -e -o pipefail; \
	for dir in $(SUBDIRS); do \
		cd $$dir && \
		uv publish --publish-url https://test.pypi.org/legacy/ --check-url=https://test.pypi.org/simple/ && \
		cd ../..; \
	done

publish:
	@set -e -o pipefail; \
	for dir in $(SUBDIRS); do \
		cd $$dir && \
		uv publish --check-url=https://pypi.org/simple/ && \
		cd ../..; \
	done

format:
	uv tool run ruff format

e2e-tests: build install
	behave tests/e2e/features && cd ..

# Create container images for the specified MCP servers
containerize:
	@for dir in $(SUBDIRS); do \
		if [[ -f $$dir/Containerfile && (-f $$dir/pyproject.toml) ]]; then \
			name=$$(uv run tomlq -r '.project.name' $$dir/pyproject.toml); \
			version=$$(uv run tomlq -r '.project.version' $$dir/pyproject.toml); \
			echo "Building container image for $$dir with version $$version"; \
			cd $$dir && \
				podman build -t $$name:$$version . && \
				podman tag $$name:$$version $$name:latest && \
				echo "Container image $$name:$$version (tagged with $$name:latest) built successfully" && cd ../..; \
		fi \
	done

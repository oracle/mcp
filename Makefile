SOURCE_FOLDER := src
COMMON_PROJECT := common
COMMON_PROJECT_PATH := $(SOURCE_FOLDER)/$(COMMON_PROJECT)
COMMON_PACKAGE := oracle-mcp-common
# These directories will be excluded from common cmds like build, install, test etc
EXCLUDED_PROJECTS := dbtools-mcp-server mysql-mcp-server oci-javascript-mcp-server oci-pricing-mcp-server oracle-db-doc-mcp-server oracle-db-mcp-java-toolkit
EXCLUDED_PROJECT_PATHS = $(addprefix $(SOURCE_FOLDER)/, $(EXCLUDED_PROJECTS))
# This matches all paths by default. If you want to run a command on a specific package you can specify the `project` variable
project ?= *
# These are the directories that will be built
DIRS := $(wildcard $(SOURCE_FOLDER)/$(project))
SUBDIRS := $(filter-out $(EXCLUDED_PROJECT_PATHS), $(DIRS))
COMMON_DIRS := $(filter $(COMMON_PROJECT_PATH),$(SUBDIRS))
SERVER_DIRS := $(filter-out $(COMMON_PROJECT_PATH),$(SUBDIRS))
# Releasing a server also releases the common dependency first, even when a
# single server is selected with `project=`.
RELEASE_DIRS := $(if $(SERVER_DIRS),$(COMMON_PROJECT_PATH) $(SERVER_DIRS),$(COMMON_DIRS))
COMMON_VERSION := $(shell uv run --isolated --no-project --python 3.13 python -c "import tomllib; print(tomllib.load(open('$(COMMON_PROJECT_PATH)/pyproject.toml', 'rb'))['project']['version'])")
JAVASCRIPT_SUBDIRS ?= $(SOURCE_FOLDER)/oci-javascript-mcp-server
NPM ?= npm

PYPI_PUBLISH_URL := https://upload.pypi.org/legacy/
PYPI_CHECK_URL := https://pypi.org/simple/
TEST_PYPI_PUBLISH_URL := https://test.pypi.org/legacy/
TEST_PYPI_CHECK_URL := https://test.pypi.org/simple/
PUBLISH_URL ?= $(PYPI_PUBLISH_URL)
PUBLISH_CHECK_URL ?= $(PYPI_CHECK_URL)
VERIFY_INDEX ?= $(PYPI_CHECK_URL)

.PHONY: build build-common build-servers publish publish-common publish-servers \
	test-publish test-publish-common test-publish-servers verify-published \
	release test-release wait-for-common _build _publish test format \
	install sync lock lock-check lint combine-coverage e2e-tests containerize \
	javascript-sync javascript-test javascript-check javascript-ci ci

build:
	@$(MAKE) _build BUILD_DIRS="$(COMMON_DIRS)"
	@$(MAKE) build-servers

build-common:
	@$(MAKE) _build BUILD_DIRS="$(COMMON_PROJECT_PATH)"

build-servers:
	@$(MAKE) _build BUILD_DIRS="$(SERVER_DIRS)"

_build:
	@set -eu; \
	for dir in $(BUILD_DIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			name=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['name'])" "$$dir/pyproject.toml") || exit 1; \
			version=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['version'])" "$$dir/pyproject.toml") || exit 1; \
			echo "Building $$dir: $$name==$$version"; \
			cd $$dir && uv build --clear && cd ../..; \
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

javascript-sync:
	@set -e; \
	for dir in $(JAVASCRIPT_SUBDIRS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Installing JavaScript dependencies in $$dir"; \
			( cd $$dir && $(NPM) install ) || exit 1; \
		fi \
	done

javascript-test:
	@set -e; \
	for dir in $(JAVASCRIPT_SUBDIRS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Testing JavaScript package in $$dir"; \
			( cd $$dir && $(NPM) test ) || exit 1; \
		fi \
	done

javascript-check:
	@set -e; \
	for dir in $(JAVASCRIPT_SUBDIRS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Checking JavaScript package in $$dir"; \
			( cd $$dir && $(NPM) run check ) || exit 1; \
		fi \
	done

javascript-ci:
	@set -e; \
	for dir in $(JAVASCRIPT_SUBDIRS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Running JavaScript CI in $$dir"; \
			( cd $$dir && $(NPM) ci && $(NPM) run ci ) || exit 1; \
		fi \
	done

ci: lint test javascript-ci

combine-coverage:
	uv run coverage combine
	uv run coverage html
	uv run coverage report --fail-under=90

publish:
	@$(MAKE) publish-common PUBLISH_URL="$(PYPI_PUBLISH_URL)" PUBLISH_CHECK_URL="$(PYPI_CHECK_URL)"
	@$(MAKE) wait-for-common VERIFY_INDEX="$(PYPI_CHECK_URL)"
	@$(MAKE) publish-servers PUBLISH_URL="$(PYPI_PUBLISH_URL)" PUBLISH_CHECK_URL="$(PYPI_CHECK_URL)"

publish-common:
	@$(MAKE) build-common
	@$(MAKE) _publish PUBLISH_DIRS="$(COMMON_PROJECT_PATH)"

publish-servers:
	@$(MAKE) build-servers
	@$(MAKE) _publish PUBLISH_DIRS="$(SERVER_DIRS)"

test-publish:
	@$(MAKE) test-publish-common
	@$(MAKE) wait-for-common VERIFY_INDEX="$(TEST_PYPI_CHECK_URL)"
	@$(MAKE) test-publish-servers

test-publish-common:
	@$(MAKE) publish-common PUBLISH_URL="$(TEST_PYPI_PUBLISH_URL)" PUBLISH_CHECK_URL="$(TEST_PYPI_CHECK_URL)"

test-publish-servers:
	@$(MAKE) publish-servers PUBLISH_URL="$(TEST_PYPI_PUBLISH_URL)" PUBLISH_CHECK_URL="$(TEST_PYPI_CHECK_URL)"

_publish:
	@set -eu; \
	publish_failed=0; \
	for dir in $(PUBLISH_DIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			echo "Publishing $$dir"; \
			if ! (cd $$dir && uv publish --publish-url "$(PUBLISH_URL)" --check-url="$(PUBLISH_CHECK_URL)"); then \
				echo "Publish failed for $$dir; continuing with remaining packages." >&2; \
				publish_failed=1; \
			fi; \
		fi; \
	done; \
	if [ "$$publish_failed" -ne 0 ]; then \
		echo "One or more package publishes failed." >&2; \
		exit 1; \
	fi

wait-for-common:
	@set -eu; \
	index_url="$$(printf '%s' "$(VERIFY_INDEX)" | sed 's:/*$$::')"; \
	for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do \
		if curl --fail --silent --show-error "$$index_url/$(COMMON_PACKAGE)/" | grep --quiet "oracle_mcp_common-$(COMMON_VERSION)"; then \
			echo "$(COMMON_PACKAGE)==$(COMMON_VERSION) is available from $$index_url"; \
			exit 0; \
		fi; \
		echo "Waiting for $(COMMON_PACKAGE)==$(COMMON_VERSION) on $$index_url (attempt $$attempt/12)"; \
		sleep 5; \
	done; \
	echo "$(COMMON_PACKAGE)==$(COMMON_VERSION) was not available from $$index_url after 60 seconds" >&2; \
	exit 1

verify-published:
	@set -eu; \
	for dir in $(RELEASE_DIRS); do \
		if [ -f $$dir/pyproject.toml ]; then \
			name=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['name'])" "$$dir/pyproject.toml") || exit 1; \
			version=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['version'])" "$$dir/pyproject.toml") || exit 1; \
			echo "Verifying $$name==$$version from $(VERIFY_INDEX)"; \
			uv run --isolated --no-project --python 3.13 --refresh-package "$$name" --index "$(VERIFY_INDEX)" --with "$$name==$$version" python -c "from importlib.metadata import version; assert version('$$name') == '$$version'"; \
		fi; \
	done

release:
	@$(MAKE) publish
	@$(MAKE) verify-published VERIFY_INDEX="$(PYPI_CHECK_URL)"

test-release:
	@$(MAKE) test-publish
	@$(MAKE) verify-published VERIFY_INDEX="$(TEST_PYPI_CHECK_URL)"

format:
	uv tool run ruff format

e2e-tests: build install
	behave tests/e2e/features && cd ..

# Create container images for the specified MCP servers
containerize:
	@for dir in $(SUBDIRS); do \
		if [[ -f $$dir/Containerfile && (-f $$dir/pyproject.toml) ]]; then \
			name=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['name'])" "$$dir/pyproject.toml") || exit 1; \
			version=$$(uv run --isolated --no-project --python 3.13 python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['version'])" "$$dir/pyproject.toml") || exit 1; \
			echo "Building container image for $$dir with version $$version"; \
			cd $$dir && \
				podman build -t $$name:$$version . && \
				podman tag $$name:$$version $$name:latest && \
				echo "Container image $$name:$$version (tagged with $$name:latest) built successfully" && cd ../..; \
		fi \
	done

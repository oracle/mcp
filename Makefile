# Project discovery and exclusions live in joist.toml.
# This matches all projects by default. Set `project` to a Joist project name to run one project.
project ?= *
base ?= origin/main
JOIST ?= python -m joist
JOIST_PROJECTS = $(if $(filter *,$(project)),--all,$(project))

.PHONY: affected-build affected-lint affected-test build combine-coverage containerize e2e-tests format install lint lock lock-check publish sync test test-publish

build:
	$(JOIST) run build $(JOIST_PROJECTS)

install:
	$(JOIST) run install $(JOIST_PROJECTS)

sync:
	$(JOIST) run sync $(JOIST_PROJECTS)

lock:
	$(JOIST) run lock $(JOIST_PROJECTS)

lock-check:
	$(JOIST) run lock-check $(JOIST_PROJECTS)

lint:
ifeq ($(project),*)
	uv tool run ruff check
else
	$(JOIST) run lint $(project)
endif

test:
	$(JOIST) run test $(JOIST_PROJECTS)
	$(MAKE) combine-coverage

combine-coverage:
	uv run coverage combine
	uv run coverage html
	uv run coverage report --fail-under=69

test-publish:
	$(JOIST) run test-publish $(JOIST_PROJECTS)

publish:
	$(JOIST) run publish $(JOIST_PROJECTS)

format:
ifeq ($(project),*)
	uv tool run ruff format
else
	$(JOIST) run format $(project)
endif

e2e-tests: build install
	behave tests/e2e/features && cd ..

# Create container images for the specified MCP servers
containerize:
	$(JOIST) run containerize $(JOIST_PROJECTS)

affected-build:
	$(JOIST) affected build --base $(base)

affected-lint:
	$(JOIST) affected lint --base $(base)

affected-test:
	$(JOIST) affected test --base $(base)

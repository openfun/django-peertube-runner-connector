# /!\ /!\ /!\ /!\ /!\ /!\ /!\ DISCLAIMER /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\
#
# This Makefile is only meant to be used for DEVELOPMENT purpose.
#
# PLEASE DO NOT USE IT FOR YOUR CI/PRODUCTION/WHATEVER...
#
# /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\
#
# Note to developpers:
#
# While editing this file, please respect the following statements:
#
# 1. Every variable should be defined in the ad hoc VARIABLES section with a
#    relevant subsection
# 2. Every new rule should be defined in the ad hoc RULES section with a
#    relevant subsection depending on the targeted service
# 3. Rules should be sorted alphabetically within their section
# 4. When a rule has multiple dependencies, you should:
#    - duplicate the rule name to add the help string (if required)
#    - write one dependency per line to increase readability and diffs
# 5. .PHONY rule statement should be written after the corresponding rule

# ==============================================================================
# VARIABLES

BOLD := \033[1m
RESET := \033[0m
GREEN := \033[1;32m

# ==============================================================================
# RULES

default: h


# -- quality

lint:  ## Run all linters (isort, black, flake8, pylint)
lint: \
	lint-isort \
	lint-black \
	lint-flake8 \
	lint-pylint \
	lint-bandit
.PHONY: lint

lint-black:  ## Run the black tool and update files that need to
	@echo "$(BOLD)Running black$(RESET)"
	black src tests
.PHONY: lint-black

lint-flake8:  ## Run the flake8 tool
	@echo "$(BOLD)Running flake8$(RESET)"
	flake8 src tests
.PHONY: lint-flake8

lint-isort:  ## automatically re-arrange python imports in code base
	@echo "$(BOLD)Running isort$(RESET)"
	isort src tests --atomic
.PHONY: lint-isort

lint-pylint:  ## Run the pylint tool
	@echo "$(BOLD)Running pylint$(RESET)"
	DJANGO_SETTINGS_MODULE=tests.app.settings DJANGO_CONFIGURATION=Test pylint --rcfile=pylintrc src tests
.PHONY: lint-pylint

lint-bandit: ## lint back-end python sources with bandit
	@echo "$(BOLD)Running bandit$(RESET)"
	bandit -c .bandit -qr src
.PHONY: lint-bandit

check-manifest: ## check the MANIFEST.in is correct
	@echo "$(BOLD)Running check-manifest$(RESET)"
	check-manifest
.PHONY: check-manifest

# -- tests

test: ## run the test suite (tox)
	@echo "$(BOLD)Running tests$(RESET)"
	tox
.PHONY: test


# -- local django server

run_django: ## run the Django test server
	@echo "$(BOLD)Running Django test server$(RESET)"
	DJANGO_ENVIRONMENT=development python tests/manage.py runserver 127.0.0.1:8000
.PHONY: run_django


# -- Misc

h: # short default help task
	@echo "$(BOLD)Project Makefile$(RESET)"
	@echo "Please use 'make $(BOLD)target$(RESET)' where $(BOLD)target$(RESET) is one of:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-50s$(RESET) %s\n", $$1, $$2}'
.PHONY: h

help:  ## Show a more readable help on multiple lines
	@echo "$(BOLD)Project Makefile$(RESET)"
	@echo "Please use 'make $(BOLD)target$(RESET)' where $(BOLD)target$(RESET) is one of:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%s$(RESET)\n    %s\n\n", $$1, $$2}'
.PHONY: help
DOCKER_IMAGE ?= ai-tutor
ENV_FILE ?= .env
DATA_DIR ?= $(PWD)/data
SET_TYPE ?=
ENV_OVERRIDES := $(if $(SET_TYPE),--env SET_TYPE=$(SET_TYPE),)

.PHONY: docker-build docker-run docker-ui

docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run:
	docker run --rm --env-file $(ENV_FILE) $(ENV_OVERRIDES) -v "$(DATA_DIR):/app/data" $(DOCKER_IMAGE) $(ARGS)

docker-ui:
	docker run --rm -p 8501:8501 --env-file $(ENV_FILE) -v "$(PWD):/app" $(ENV_OVERRIDES) --entrypoint streamlit $(DOCKER_IMAGE) run frontend/streamlit_app.py --server.address=0.0.0.0 --server.port=8501

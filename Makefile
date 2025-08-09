.PHONY: venv activate tf-init-dev tf-validate

venv:
	python3 -m venv .venv

activate:
	@echo "Ejecuta: source .venv/bin/activate"

tf-init-dev:
	cd infra/terraform/envs/dev && terraform init

tf-validate:
	cd infra/terraform/envs/dev && terraform validate || true

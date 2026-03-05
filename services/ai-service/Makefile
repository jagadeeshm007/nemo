.PHONY: run test lint proto clean

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	ruff check app/ tests/
	mypy app/

proto:
	python -m grpc_tools.protoc \
		-I../../proto \
		--python_out=app/infrastructure/grpc/generated \
		--grpc_python_out=app/infrastructure/grpc/generated \
		../../proto/ai/v1/AiService.proto

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache

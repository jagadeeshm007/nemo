.PHONY: build run test lint proto clean migrate-up migrate-down

APP_NAME=api-gateway
BUILD_DIR=./bin

build:
	CGO_ENABLED=0 go build -ldflags="-w -s" -o $(BUILD_DIR)/$(APP_NAME) ./cmd/gateway/main.go

run:
	go run ./cmd/gateway/main.go

test:
	go test -v -race -cover ./...

lint:
	golangci-lint run ./...

proto:
	protoc --go_out=. --go-grpc_out=. \
		../../proto/ai/v1/AiService.proto \
		../../proto/plugin/v1/PluginService.proto \
		../../proto/workflow/v1/WorkflowService.proto \
		../../proto/vector/v1/VectorService.proto

clean:
	rm -rf $(BUILD_DIR)

migrate-up:
	go run ./cmd/migrate/main.go up

migrate-down:
	go run ./cmd/migrate/main.go down

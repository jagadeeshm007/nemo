# ==============================================================================
# API Gateway — Dockerfile
# ==============================================================================

FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o /bin/api-gateway \
    ./cmd/gateway/main.go

# ---------------------------------------------------------------------------

FROM alpine:3.19

RUN apk add --no-cache ca-certificates tzdata

COPY --from=builder /bin/api-gateway /bin/api-gateway

EXPOSE 8080 9090

ENTRYPOINT ["/bin/api-gateway"]

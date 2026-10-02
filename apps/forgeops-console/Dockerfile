# Build from the repository root so both halves see the same source tree.
FROM node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 AS browser
WORKDIR /src
COPY apps/forgeops-console/web/package.json apps/forgeops-console/web/package-lock.json ./apps/forgeops-console/web/
RUN cd apps/forgeops-console/web && npm ci
COPY apps/forgeops-console ./apps/forgeops-console
RUN cd apps/forgeops-console/web && npm run build

FROM golang:1.27-alpine@sha256:8a5910f31396cd4d89662f56c68b3ae31d374308270a1c3bd96672ee5ed43414 AS builder
WORKDIR /src/apps/forgeops-console
COPY apps/forgeops-console/go.mod apps/forgeops-console/go.sum ./
RUN go mod download
COPY apps/forgeops-console ./
COPY --from=browser /src/apps/forgeops-console/web/dist ./web/dist
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /out/forgeops-console ./cmd/forgeops-console

FROM scratch
COPY --from=builder /out/forgeops-console /forgeops-console
COPY --from=browser /src/apps/forgeops-console/web/dist /web
USER 65532:65532
EXPOSE 9090
ENTRYPOINT ["/forgeops-console"]
CMD ["--in-cluster", "--web-dir", "/web"]

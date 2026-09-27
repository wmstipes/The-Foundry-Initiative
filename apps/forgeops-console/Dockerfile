# Build from the repository root so both halves see the same source tree.
FROM node:24-alpine AS browser
WORKDIR /src
COPY apps/forgeops-console/web/package.json apps/forgeops-console/web/package-lock.json ./apps/forgeops-console/web/
RUN cd apps/forgeops-console/web && npm ci
COPY apps/forgeops-console ./apps/forgeops-console
RUN cd apps/forgeops-console/web && npm run build

FROM golang:1.27-alpine AS builder
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

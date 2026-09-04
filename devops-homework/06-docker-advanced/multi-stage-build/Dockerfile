# --- Stage 1: build ---
# Full Go toolchain (~800MB+) - only needed to COMPILE the binary.
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY main.go .
# CGO_ENABLED=0 -> fully static binary, no libc dependency at runtime,
# which is what lets us run it on a "scratch" (empty) base image below.
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/server main.go

# --- Stage 2: run ---
# `scratch` is a literally empty base image - no shell, no package manager,
# nothing but our one static binary. Only the compiled artifact is copied
# over from the build stage; the entire Go toolchain is left behind.
FROM scratch
COPY --from=build /out/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]

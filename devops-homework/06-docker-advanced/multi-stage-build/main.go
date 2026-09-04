package main

import (
	"fmt"
	"net/http"
)

// The assignment requires the container to serve the exact string
// "Hello World from Docker multi-stage build" on port 8080.
const message = "Hello World from Docker multi-stage build"
const port = "8080"

func handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w, "<!doctype html>\n<html>\n<head><title>Multi-stage build</title></head>\n<body>\n<h1>%s</h1>\n<p>Served from a multi-stage-built Docker image on port %s.</p>\n</body>\n</html>\n", message, port)
}

func main() {
	http.HandleFunc("/", handler)
	fmt.Printf("server listening on port %s\n", port)
	http.ListenAndServe(":"+port, nil)
}

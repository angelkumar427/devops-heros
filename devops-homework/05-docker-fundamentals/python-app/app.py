from http.server import BaseHTTPRequestHandler, HTTPServer

class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hello World from Python!</h1><p>Served by a Docker container.</p>\n")

if __name__ == "__main__":
    port = 5000
    server = HTTPServer(("0.0.0.0", port), HelloHandler)
    print(f"Python hello-world server listening on port {port}")
    server.serve_forever()

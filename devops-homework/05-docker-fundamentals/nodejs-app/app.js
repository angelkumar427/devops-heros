const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end('<h1>Hello World from Node.js!</h1><p>Served by a Docker container.</p>\n');
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Node.js hello-world server listening on port ${PORT}`);
});

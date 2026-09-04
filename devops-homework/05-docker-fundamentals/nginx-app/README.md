# Nginx — Hello World

| | |
|---|---|
| Base image | `nginx:alpine` |
| App | [`index.html`](./index.html) — a static page, copied into Nginx's document root `/usr/share/nginx/html/` |
| Container port | 80 (published on 8082) |

Same shape as the Apache exercise, but with the other mainstream web server — the only difference that matters here is the document root path (`/usr/share/nginx/html` vs Apache's `/usr/local/apache2/htdocs`).

## Build & run

```bash
docker build -t hello-nginx .
docker run -d --name hello-nginx -p 8082:80 hello-nginx
curl http://localhost:8082
```

Expected: the "Hello World from Nginx" page.

Verified transcript: [`../run-and-verify-all.txt`](../run-and-verify-all.txt)

## Screenshot

The running container serving the page in a browser:

![Nginx Hello World](../screenshots/nginx-app.png)

# A minimal "Hello World" React app. Instead of running an npm/vite build
# step inside the image (adds a heavy toolchain + network dependency at
# build time), React and ReactDOM's production UMD builds are vendored
# locally and the whole thing is served as static files by Nginx.
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY react.production.min.js /usr/share/nginx/html/react.production.min.js
COPY react-dom.production.min.js /usr/share/nginx/html/react-dom.production.min.js

EXPOSE 80

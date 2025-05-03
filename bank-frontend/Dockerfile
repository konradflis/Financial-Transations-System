# frontend/Dockerfile

FROM node:18 as build

WORKDIR /app

COPY bank-frontend/package*.json ./
RUN npm install

COPY bank-frontend .

RUN npm run build

# Etap serwera statycznego
FROM --platform=linux/arm64 nginx:alpine

COPY bank-frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
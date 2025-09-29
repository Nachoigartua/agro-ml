# Build stage
FROM node:20-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY dist/webapp/browser /usr/share/nginx/html
EXPOSE 80

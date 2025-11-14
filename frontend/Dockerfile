FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 4200
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4200"]

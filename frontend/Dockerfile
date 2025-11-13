FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/frontend-entrypoint.sh
RUN chmod +x /usr/local/bin/frontend-entrypoint.sh

EXPOSE 4200
ENTRYPOINT ["frontend-entrypoint.sh"]
CMD ["npm", "run", "start:docker"]

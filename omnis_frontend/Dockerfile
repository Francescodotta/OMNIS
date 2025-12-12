FROM node:24-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN if [ -d node_modules/.bin ]; then find node_modules/.bin -type f -exec chmod +x {} +; fi

ENV CHOKIDAR_USEPOLLING=true
EXPOSE 3000
CMD ["npm", "start"]
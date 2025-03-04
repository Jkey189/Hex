FROM node:18-buster

COPY . /app

WORKDIR /app

RUN npm install

RUN npm run build

# Add a health check to ensure the server is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s CMD curl -f http://localhost:3000 || exit 1

CMD ["npm", "run", "dev"]
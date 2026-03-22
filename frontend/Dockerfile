FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Environment variables should be passed at runtime or build time
CMD ["npm", "run", "dev"]

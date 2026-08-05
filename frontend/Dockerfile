FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache curl

COPY package*.json ./
# react-query@3 declares a peer dependency on React <=18; this project
# runs React 19, so a plain `npm install` fails ERESOLVE. The same
# conflict exists locally - --legacy-peer-deps is how the working
# node_modules here was actually installed.
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

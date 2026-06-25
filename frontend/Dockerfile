FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --no-audit --no-fund --maxsockets=3 \
    --fetch-timeout=60000 --fetch-retries=5 --fetch-retry-maxtimeout=120000 \
    --loglevel=http

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

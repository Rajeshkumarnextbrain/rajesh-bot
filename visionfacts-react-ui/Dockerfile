# Build stage
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
# Clean install
RUN npm ci

COPY . .
# Pass build-time environment variables if needed
ARG VITE_API_HOST
ENV VITE_API_HOST=$VITE_API_HOST

RUN npm run build

# Production stage
FROM nginx:stable-alpine
# Copy custom nginx config to support React Router (if needed)
# COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/tsconfig.json frontend/next.config.js frontend/postcss.config.js frontend/tailwind.config.js frontend/.eslintrc.json frontend/next-env.d.ts ./
COPY frontend/components ./components
COPY frontend/pages ./pages
COPY frontend/public ./public
COPY frontend/styles ./styles

RUN npm install && npm run export

FROM nginx:1.25-alpine AS runtime

COPY --from=build /app/out /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


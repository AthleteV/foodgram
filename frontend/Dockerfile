# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY . ./
RUN npm install
RUN npm run build
CMD ["cp", "-r", "build", "result_build"]

# Build stage on the current Node LTS. Node and node_modules stay in this
# stage and do not reach the final image.
FROM node:24-alpine AS build
WORKDIR /app
# yarn.lock is the lockfile that matches package.json; --frozen-lockfile
# fails the build instead of resolving other versions.
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --non-interactive
COPY . ./
RUN yarn build

# Final stage: the built files and a shell to copy them into the directory
# that nginx serves.
FROM busybox:1.37
WORKDIR /app
COPY --from=build /app/build ./build
CMD ["cp", "-r", "build", "result_build"]

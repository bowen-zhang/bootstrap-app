# Bootstrap Instructions

## Initial Setup

### Essential Files

Create the following essential files with pre-populated content.

- /requirements.txt: use this file to keep tracking all the python libraries used by the project. Initialize it with connectrpc, fastapi, grpcio-tools, protoc-gen-connectrpc.

    > Do NOT use protoc-gen-connect-python. It is older plugin and will cause codec
    > issues.

- .gitignore: use this file to tell github what files to ignore. Initialize it with ".venv", "**/__pycache__", "**/node_modules", "protos/*_pb2.py*", "protos/*_connect.py*", "web/src/libs/*_pb.ts", "web/dist".

- Makefile: use it to build recursively and run services.

### Python Virtual Environment

Create a python virtual environment as:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Settings

1. Add domain name and admin email to settings-template.yaml.


## System Interface

1. Create /protos directory to store all protobuf files for interface definition.
1. Create a .proto file inside to define service interface and data structures.

    > Best practice: use a version number in "package" settings, such as "app.v1".

1. Create /protos/Makefile with the following rules to generate python and javascript files.

    ```makefile
    python:
        protoc \
            -I . \
            --python_out=. \
            --connectrpc_out=protobuf=google:. \
            *.proto
    js:
        protoc \
            -I . \
            --es_out=../web/src/libs \
            --es_opt=target=ts \
            *.proto
    ```

    > NOTE: set "protobuf=google", otherwise ConnectRPC will use protobuf-py codec
    > which is a mismatch to google.protobuf codec used in generated message _pb2.py.

1. Install Connect Web proto generation plugins.

    ```
    npm install @bufbuild/protoc-gen-es @connectrpc/connect-web
    ```

1. Build protos

## API Server

Use a dedicated API server to decouple between use-facing apps and various backend services.

The API server is built in Python using FastAPI and Connect Web.

The API server can expose multiple services defined in protobuf. Each service is focused on one logical set of operations.

1. Create /services/api directory for API server.
1. Create a [name]_service.py file in it for each service.
1. In each [name]_service.py file, create a Service class and drive from generated service class in corresponding protos/*_pb2.py. Implement its methods.
1. Create main.py. Create a FastAPI instance, mount each generated *ASGIApplication class instance to it.

    ```python
    app = fastapi.FastAPI()
    greeting_service_app = api_connect.GreetingServiceASGIApplication(GreetingService())
    app.mount('/app.v1.GreetingService', greeting_service_app)
    ```

1. Use uvicorn to launch it.

    ```python
        uvicorn.run(
        "main:create_app",
        factory=True,
        host="localhost", 
        port = int(os.getenv("PORT", "50051")),
        reload=settings.is_dev
    )
    ```

    > Note that:
    > - application: has to be passed in as a string for reload to work.
    > - factory: set to True to eliminate a warning.
    > - reload: allow FastAPI to detect source code changes and auto reload. Make sure to set it to False in production.

1. Create Makefile with default rule to run API server.

## Reverse Proxy

Nginx is used as reverse proxy to:

- Serve web app
- Reverse proxy API traffic to API server

Two nginx configurations will be set up, one for local development, another for production.

**To set up local development:**

1. Create /nginx directory to keep all reverse proxy related files.
1. Create SSL certificate for localhost:

    ```bash
	brew install mkcert nss
	mkcert -install
	mkcert localhost 127.0.0.1 ::1    
    ```

1. Create /nginx/nginx-dev.conf with the following settings:
    - listen to 8080 with ssl (to enable https).
    - use created certificate and key, specify ssl session cache and timeout.
    - for traffic to "/", pass-through to http://localhost:3000.
    - for traffic to "/api", pass-through to http://localhost:50051, use http version 1.1, turn off buffering, turn on trailer support.
    - set access log to "logs/access.log".

1. Create Makefile with a default rule to run nginx as:

    ```bash
    exec nginx -p $(CURRNET_DIR) -e logs/error.log -c nginx-dev.conf -g 'daemon off;'
    ```

## Web App

The web app is a Vue app with Vuetify and Vue router.

1. Create /web directory for the web app.
1. Bootstrap Vue app

    ```bash
    npm create vuetify@latest
    ```

1. Install NPM packages and dependencies

    ```bash
    npm install
    npm install @connectrpc/connect @connectrpc/connect-web

1. Import and call API service.

    ```typescript
    import { createClient } from "@connectrpc/connect";
    import { createGrpcWebTransport } from "@connectrpc/connect-web";
    import { GreetingService } from "../libs/api_pb";

    const transport = createGrpcWebTransport({
        baseUrl: `${window.location.origin}/api`,
    });

    const client = createClient(GreetingService, transport);
    client.greet({ name: "Connect" }).then((response) => {
        console.log(response.message);
    });
    ```

1. Create Makefile with build and run rules to build and run development server.
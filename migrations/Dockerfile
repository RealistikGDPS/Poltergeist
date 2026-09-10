FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends default-mysql-client wget ca-certificates && rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/golang-migrate/migrate/releases/download/v4.18.3/migrate.linux-amd64.tar.gz && \
    tar zxf migrate.linux-amd64.tar.gz && \
    mv migrate /usr/local/bin/go-migrate && \
    chmod u+x /usr/local/bin/go-migrate && \
    rm migrate.linux-amd64.tar.gz

WORKDIR /app
COPY perform_migrations.sh /app/perform_migrations.sh
RUN chmod +x /app/perform_migrations.sh
COPY ./migrations /migrations

ENTRYPOINT [ "/app/perform_migrations.sh" ]

FROM python:3.9.1-slim-buster

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd -m -g app --uid 10001 -s /usr/sbin/nologin app

COPY . /app

RUN apt-get update && \
    pip install -U pip && \
    pip install -r requirements.txt && \
    pip install . && \
    apt-get -q --yes autoremove && \
    apt-get clean && \
    rm -rf /root/.cache

ENTRYPOINT ["/app/scripts/run.sh"]
CMD ["server"]

# run as non priviledged user
USER app

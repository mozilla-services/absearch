FROM python:2.7-stretch

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd -g app --uid 10001 -s /usr/sbin/nologin app

COPY . /app

RUN python ./setup.py install

# run the server with the baked in default configuration
# volume mount over /app/config/absearch.ini to over-ride the
# configuration
ENTRYPOINT ["/usr/local/bin/absearch-server"]
CMD ["/app/config/absearch.ini"]

# run as non priviledged user
USER app

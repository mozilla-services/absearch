FROM python:2.7-stretch

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd -g app --uid 10001 -s /usr/sbin/nologin app


COPY ./dev-requirements.txt /app/dev-requirements.txt

# Copy in the whole app after dependencies have been installed & cached
COPY . /app
RUN python ./setup.py install

# run the server by default
ENTRYPOINT ["/usr/local/bin/absearch-server"]
CMD ["/app/config/absearch.ini"]

# run as non priviledged user
USER app

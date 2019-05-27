FROM python:2.7-slim-stretch

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd -m -g app --uid 10001 -s /usr/sbin/nologin app

COPY . /app

# note: install gevent as a binary package to prevent the need
# for gcc and compiling from src (container bloat).
# setup.py should require the same version of gcc that
# comes as a package (1.1.2)
RUN apt-get update && \
    apt-get install -y python-gevent && \
    python ./setup.py install && \
    apt-get -q --yes autoremove && \
    apt-get clean && \
    rm -rf /root/.cache

ENTRYPOINT ["/app/scripts/run.sh"]
CMD ["server"]

# run as non priviledged user
USER app

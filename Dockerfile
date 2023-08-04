FROM python:3.9.16

RUN useradd -m -u 1000 -s /bin/bash python \
    && mkdir /app \
    && chown -R python /app

ENV PATH /home/python/.local/bin:$PATH

COPY --chown=python . /app

USER python

WORKDIR /app

RUN git submodule update --init \
    && pip install -r ./requirements.txt

EXPOSE 8000

CMD ["/bin/bash", "-c", "/app/docker-entrypoint.sh"]

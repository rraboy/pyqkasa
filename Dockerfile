FROM python:3.9

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install pipenv -y
RUN useradd -ms /bin/bash pyqkasa

WORKDIR /opt/pyqkasa
RUN chown pyqkasa /opt/pyqkasa
COPY --chown=pyqkasa *.py ./
COPY --chown=pyqkasa Pipfile* ./
COPY --chown=pyqkasa logging.ini ./
USER pyqkasa
RUN pipenv install

ENTRYPOINT [ "/bin/bash", "-c" ]
CMD [ "pipenv run python main.py" ]

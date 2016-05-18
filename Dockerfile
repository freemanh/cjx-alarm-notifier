FROM python:2.7.11

RUN pip install beanstalkc
RUN pip install PyYAML
RUN pip install python-dateutil

ADD . /code
WORKDIR /code

CMD [ "python", "cjx-alarm-notifier.py" ]
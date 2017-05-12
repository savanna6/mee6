FROM python:3
RUN mkdir mee6
ADD . /mee6/
RUN cd /mee6 && pip3 install .
RUN rm -rf /mee6

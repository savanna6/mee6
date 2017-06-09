FROM python:3
RUN mkdir mee6
ADD requirements.txt /mee6/requirements.txt
RUN cd /mee6 && pip3 install -r requirements.txt
ADD . /mee6/
RUN cd /mee6 && pip3 install .
RUN rm -rf /mee6

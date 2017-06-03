FROM python:3

ENV SRVHOME=/srv

ENV SRVPROJ=/srv/AstroSite

RUN mkdir logs
VOLUME ["$SRVHOME/logs/"]

COPY . $SRVPROJ

RUN apt-get update
RUN apt-get install -y python3-numpy python3-scipy python3-matplotlib
RUN pip install -r $SRVPROJ/requirements.txt
RUN pip install --no-deps 'astropy==1.3'
RUN pip install astroquery
RUN pip install --no-deps photutils

EXPOSE 80

WORKDIR $SRVPROJ

COPY startserver.sh /

ENTRYPOINT ["/startserver.sh"]

#COPY DockerTest.py /
#CMD ["python", "/DockerTest.py"]

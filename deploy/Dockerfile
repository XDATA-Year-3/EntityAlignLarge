FROM ubuntu:14.04
MAINTAINER David Manthey <david.manthey@kitware.com>

# The environment variables beginning with KWDEMO can be used to map this demo
# to the main url space.  See the end of this file.
ENV KWDEMO_READY FALSE

EXPOSE 8080

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libffi-dev \
    libpq-dev \
    libpython-dev \
    python-pip \
    python-software-properties \
    software-properties-common \
    vim

# Get nodejs apt source
RUN curl -sL https://deb.nodesource.com/setup | sudo bash -

# Install packages requiring additional sources
RUN apt-get update && apt-get install -y \
    nodejs

RUN npm install -g npm@next && \
    npm --version

RUN npm install -g grunt-cli

# bower does't work particularly well as root, so we create a non-root user
# called kwuser, but give it sudo ability.
RUN adduser --disabled-password --gecos '' kwuser && \
    adduser kwuser sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER kwuser

WORKDIR /home/kwuser

RUN mkdir /home/kwuser/logs

# XDATA's proxy can't use the git protocol
RUN git config --global url."https://".insteadOf git://

RUN git clone git://github.com/XDATA-Year-3/EntityAlignLarge && \
    cd EntityAlignLarge && \
    git checkout 89ae2ac3cd4fdd4e6ea97889df446557d56adc3b && \
    git reset --hard
WORKDIR /home/kwuser/EntityAlignLarge
ENV PATH $PATH:/home/kwuser/.local/bin
RUN pip install --user tangelo elasticsearch pymongo python-Levenshtein

COPY makelocalcfg.py /home/kwuser/makelocalcfg.py

ENV KWDEMO_NAME Resonant Document Ranking
ENV KWDEMO_KEY resdoc
ENV KWDEMO_DESC Resonant Document Ranking application
ENV KWDEMO_IMG /resdoc/built/thumb.jpg
ENV KWDEMO_READY TRUE

CMD ["sh", "-c", "python /home/kwuser/makelocalcfg.py > defaults.json && tangelo --hostname='0.0.0.0' -c tangelo-config.yaml 2>&1 | tee /home/vagrant/resonant_output.log"]

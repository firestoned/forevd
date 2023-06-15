FROM httpd:2.4

RUN apt-get update

RUN apt-get install --no-install-recommends -y \
    ca-certificates libapache2-mod-auth-openidc \
    python3 pip curl

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN apt-get --yes remove curl

RUN ln -sf /usr/lib/apache2/modules/mod_auth_openidc.so /usr/local/apache2/modules/mod_auth_openidc.so

COPY . /usr/local/forevd
RUN rm -rf /usr/local/forevd/dist

WORKDIR /usr/local/forevd

ENV PATH="$PATH:/root/.local/bin"
RUN poetry install
RUN poetry build

ENV PIP_BREAK_SYSTEM_PACKAGES 1
RUN pip install --verbose --upgrade dist/forevd-*.whl

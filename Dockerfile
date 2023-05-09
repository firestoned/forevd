FROM httpd:2.4

RUN apt-get update

RUN apt search python

RUN apt-get install --no-install-recommends -y \
    ca-certificates libapache2-mod-auth-openidc \
    python3 pip

RUN ln -sf /usr/lib/apache2/modules/mod_auth_openidc.so /usr/local/apache2/modules/mod_auth_openidc.so

RUN pip install poetry

COPY . /usr/local/forevd
WORKDIR /usr/local/forevd

RUN poetry install
RUN poetry build
RUN pip install --verbose dist/forevd-*.whl

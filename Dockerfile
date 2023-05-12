FROM httpd:2.4

RUN apt-get update

RUN apt-get install --no-install-recommends -y \
    ca-certificates libapache2-mod-auth-openidc \
    python3 pip

RUN ln -sf /usr/lib/apache2/modules/mod_auth_openidc.so /usr/local/apache2/modules/mod_auth_openidc.so

COPY . /usr/local/forevd
RUN rm -rf /usr/local/forevd/dist

WORKDIR /usr/local/forevd

RUN pip install poetry
RUN poetry install
RUN poetry build
RUN ls -al /usr/local/forevd/dist
RUN pip install --verbose --upgrade dist/forevd-*.whl

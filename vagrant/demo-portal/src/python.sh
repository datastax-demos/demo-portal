#!/bin/sh

# install Python 2.7.8+
if [ ! -f /portal/python/bin/python ]; then

    CACHE=/cache/apt/python
    if [ ! -d ${CACHE} ]; then
        mkdir -p ${CACHE}
        PACKAGES='libsqlite3-dev libbz2-dev libgdbm-dev libncurses5-dev tk-dev libreadline-dev libdb5.1-dev libssl-dev'
        apt-get --print-uris --yes install $PACKAGES | grep ^\' | cut -d\' -f2 > ${CACHE}.list
        wget -c -i ${CACHE}.list -P ${CACHE}
    fi
    sudo dpkg -i ${CACHE}/*

    if [ ! -d /cache/python ]; then
        (
            cd /cache
            wget -c http://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
            tar -zxvf Python-2.7.9.tgz

            cd /cache/Python-2.7.9
            mkdir /portal/python
            ./configure --prefix=/portal/python
            make
            make install
        )

        cp -r /portal/python /cache/
    else
        cp -r /cache/python /portal/
    fi

    echo "export PATH=/portal/python/bin:$PATH" >> .profile
fi

# setup virtualenv
if [ ! -f /portal/virtualenv/bin/activate ]; then
    wget -c https://pypi.python.org/packages/source/v/virtualenv/virtualenv-12.0.5.tar.gz#md5=637abbbd04d270ee8c601ab29c4f7561 -P /cache

    (
        cd /tmp
        tar -zxvf /cache/virtualenv-12.0.5.tar.gz

        cd virtualenv-12.0.5/
        /portal/python/bin/python setup.py install
        /portal/python/bin/virtualenv /portal/virtualenv --python /portal/python/bin/python2.7
    )

    echo "source /portal/virtualenv/bin/activate" >> .profile
fi

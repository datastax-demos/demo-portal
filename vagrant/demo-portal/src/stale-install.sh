#!/bin/sh

chmod 600 .ssh/*
ssh-keyscan github.com >> .ssh/known_hosts

cd /portal
git clone git@demo-portal:datastax-demos/demo-portal.git

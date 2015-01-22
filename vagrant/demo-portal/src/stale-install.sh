#!/bin/sh

chmod 600 .ssh/*

cd /portal
git clone git@demo-portal:datastax-demos/demo-portal.git

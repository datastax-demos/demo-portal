#!/bin/sh

chmod 600 .ssh/*

git clone --branch production git@demo-portal:datastax-demos/demo-portal.git /portal/demo-portal

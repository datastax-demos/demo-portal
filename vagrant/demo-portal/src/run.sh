#!/bin/sh

if [ -n "$PRODUCTION" ]; then
    # kick off the demo-portal
    nohup python /portal/demo-portal/flask2.0/run > out.log 2>&1 &
fi

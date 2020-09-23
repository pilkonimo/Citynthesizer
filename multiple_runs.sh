#!/bin/bash
RUNS=20
until [ $RUNS -lt 1 ]; do
    ./blender ~/BA/deployment/standard.blend -b -P ~/BA/deployment/setup.py
    let RUNS-=1
done

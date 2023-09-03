#!/bin/sh

for i in mutable-keyboards; do
  python generate-$i.py $i.yaml
done

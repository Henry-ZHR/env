#!/bin/sh

for i in liquid-keyboard; do
  python generate-$i.py $i.yaml
done

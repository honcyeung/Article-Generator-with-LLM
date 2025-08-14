#!/bin/bash

jupyter nbconvert main.ipynb --to script --output "main"
chmod a+x main.py
sed -i '' '/^# In/d' main.py
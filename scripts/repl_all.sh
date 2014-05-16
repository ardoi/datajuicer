#!/bin/bash
echo "Replacing $1 with $2"
find . -type f -name "*.py"|xargs sed -i -e 's|$1|$2|g'

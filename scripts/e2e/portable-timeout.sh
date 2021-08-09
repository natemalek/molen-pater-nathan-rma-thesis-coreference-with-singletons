if hash timeout 2>/dev/null; then
    timeout -s 9 "$@"
elif hash gtimeout 2>/dev/null; then
    gtimeout -s 9 "$@"
else
    echo Please install coreutils
    exit 1
fi

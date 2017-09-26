#! /bin/sh

echo "info line 1"
echo "error line 1"  >&2
echo "info line 2" 
echo "info line 2" 
echo "error line 2"  >&2
echo "error line 2"  >&2
echo "info line 3" 
echo "info line 3" 
echo "info line 3" 
echo "error line 3"  >&2
echo "error line 3"  >&2
echo "error line 3"  >&2
echo "info line 4" 
echo "info line 4" 
echo "info line 4" 
echo "info line 4" 
echo "error line 4"  >&2
echo "error line 4"  >&2
echo "error line 4"  >&2
echo "error line 4"  >&2

read arga
echo ${arga}
read argb
echo ${argb}
read argc
echo ${argc}

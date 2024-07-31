#!/bin/sh

docker container run -d -it --name shmpd --mount type=bind,src=/home/"${HOME}"/Documents/github/sh-mpd,dst=/home/shmpd/Documents/github/sh-mpd -p 80:80 sh-mpd_amd64


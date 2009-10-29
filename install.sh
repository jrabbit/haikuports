#!/bin/sh
alert --idea "Install haikuporter?" Yes No > /dev/null
button=$?
if [ $button -eq 0 ] ; then
  		cp haikuporter $(finddir B_COMMON_BIN_DIRECTORY)/haikuporter > /dev/null
  		cp haikuports.conf $(finddir B_COMMON_ETC_DIRECTORY)/haikuports.conf > /dev/null
  		alert "haikuporter is ready." > /dev/null
else
		alert --stop "haikuporter is not installed." > /dev/null
fi

#!/usr/bin/env bash 
echo performing customization tasks with param $1 at `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"` >> /root/customization.log
if [ x$1=x"precustomization" ];
then
  echo performing precustomization tasks on `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"`
  echo performing precustomization tasks on `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"` >> /root/customization.log
fi
if [ x$1=x"postcustomization" ];
then
  echo performing postcustomization tasks at `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"`
  echo performing postcustomization tasks at `date "+DATE: %Y-%m-%d - TIME: %H:%M:%S"` >> /root/customization.log
fi

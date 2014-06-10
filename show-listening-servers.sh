#!/bin/bash

lsof -i -s TCP:LISTEN -nP +c0

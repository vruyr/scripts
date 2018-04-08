#!/usr/bin/env bash

echo --- Homebrew
brew outdated --verbose
echo --- Homebrew Cask
brew cask outdated --verbose --greedy
echo --- Mac App Store
softwareupdate --list
echo ...

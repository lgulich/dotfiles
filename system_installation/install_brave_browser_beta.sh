#!/bin/sh

set -ex

sudo apt-get install -y apt-transport-https curl

curl -s https://brave-browser-apt-beta.s3.brave.com/brave-core-nightly.asc \
  | sudo apt-key --keyring /etc/apt/trusted.gpg.d/brave-browser-prerelease.gpg add -

echo "deb [arch=amd64] https://brave-browser-apt-beta.s3.brave.com/ stable main" \
  | sudo tee /etc/apt/sources.list.d/brave-browser-beta.list

sudo apt-get update
sudo apt-get install -y brave-browser-beta

#!/bin/sh

set -e

wget -O- https://packages.microsoft.com/keys/microsoft.asc | \
  sudo gpg --dearmor | \
  sudo tee /usr/share/keyrings/vscode.gpg

echo deb [arch=amd64 signed-by=/usr/share/keyrings/vscode.gpg] https://packages.microsoft.com/repos/vscode stable main | \
  sudo tee /etc/apt/sources.list.d/vscode.list

sudo apt-get update
sudo apt-get install -y code

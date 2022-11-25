#!/bin/sh

set -e


cd /tmp

curl -sSO https://downloads.1password.com/linux/tar/stable/x86_64/1password-latest.tar.gz
tar -xf 1password-latest.tar.gz
sudo rm -rf /opt/1Password
sudo mkdir -p /opt/1Password
sudo mv -f 1password-*/* /opt/1Password
sudo /opt/1Password/after-install.sh
1password --version  # To verify installation


ARCH="amd64"
wget "https://cache.agilebits.com/dist/1P/op2/pkg/v2.0.0/op_linux_${ARCH}_v2.0.0.zip" -O op.zip
unzip -d op op.zip
sudo mv -f op/op /usr/local/bin
rm -r op.zip op

op --version  # To verify installation

sudo groupadd onepassword-cli || true
sudo chown root:onepassword-cli /usr/local/bin/op
sudo chmod g+s /usr/local/bin/op

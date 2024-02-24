sudo apt-get update
sudo apt-get upgrade
sudo apt install vim tmux cmake

cp tmux_config.txt ~/.tmux.conf
cp vimrc.txt ~/.vimrc

echo "export EDITOR=vim" >> ~/.bashrc

pip install -r requirements.txt --break-system-packages

#sh openvins_setup.sh

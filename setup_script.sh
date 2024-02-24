sudo apt-get update
sudo apt-get upgrade
sudo apt install vim tmux cmake

cp tmux_config.txt ~/.tmux.conf
cp vimrc.txt ~/.vimrc

echo "export EDITOR=vim" >> ~/.bashrc

#sh openvins_setup.sh

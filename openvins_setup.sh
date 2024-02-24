sudo apt-get install libeigen3-dev libboost-all-dev libceres-dev libopencv-dev

cd ~
git clone https://github.com/rpng/open_vins/
cd open_vins/ov_msckf/
mkdir build ; cd build
cmake -DENABLE_ROS=OFF ..
make -j2
sudo make install

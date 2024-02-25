- /hacker_src holds source code, camera parameters, and running script
    - hacker.cc contains all source code of the SLAM module
    - run_hacker.sh runs hacker with the default ip address, port, etc.
    - See https://github.com/raulmur/ORB_SLAM2?tab=readme-ov-file#tum-dataset for what the command line arguments of hacker do
    - hacker.yml contains the calibration data of the camera

- To build hacker, run /build.sh
- To run hacker, first build, then go into /hacker_src and do ./run_hacker.sh or manually do ./hacker <arguments>
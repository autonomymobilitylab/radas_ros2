FROM osrf/ros:jazzy-desktop

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    python3-venv \
    python3-git \
    python3 \
    python3-dotenv \
    python3-serial \
    git \
    wget \
    iproute2 \
    libasio-dev \
    build-essential \
    cmake \
    libusb-1.0-0-dev \
    libudev-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libboost-all-dev \
    libgeographiclib-dev \
    libcap-dev \
    rtklib \
    ros-jazzy-diagnostic-updater \
    ros-jazzy-pcl-ros \
    ros-jazzy-nmea-msgs \
    ros-jazzy-rtcm-msgs \
    ros-jazzy-camera-info-manager \
    ros-jazzy-cv-bridge \
    ros-jazzy-diagnostic-aggregator \
    ros-jazzy-cv-bridge \
    ros-jazzy-multisensor-calibration \
    ros-jazzy-camera-calibration \
    ros-jazzy-mavros-msgs \
    ros-jazzy-gps-msgs \
    ros-jazzy-gtest-vendor \
    ros-jazzy-septentrio-gnss-driver \
    ros-jazzy-image-transport \
    ros-jazzy-compressed-image-transport \
    && rm -rf /var/lib/apt/lists/*

# Install Pylon SDK
RUN wget -q "https://downloads-bsl.baslerweb.com/software/pylon%2026.04/pylon-26.04.1_linux-x86_64_debs.tar.gz" -O /tmp/pylon.tar.gz && \
    mkdir -p /tmp/pylon && \
    tar -xzf /tmp/pylon.tar.gz -C /tmp/pylon && \
    apt-get update && \
    dpkg -i /tmp/pylon/*.deb || apt-get install -f -y && \
    rm -rf /tmp/pylon /tmp/pylon.tar.gz && \
    rm -rf /var/lib/apt/lists/*

# Set up the underlaying package workspace
WORKDIR /underlay_ws
RUN mkdir -p src

# Clone Hesai and Pylon
RUN git clone --recursive https://github.com/HesaiTechnology/HesaiLidar_ROS_2.0.git src/hesai_ros_driver && \
    git clone https://github.com/basler/pylon-ros-camera.git src/pylon-ros2-camera && \
    git clone -b ros2 https://github.com/qti-weijshen/Xsens_MTi_ROS_Driver_and_Ntrip_Client.git src/xsens-mti-ros2

# Install dependencies using rosdep
RUN apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# Build the workspace
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install --event-handlers console_direct+

# Source the ROS 2 setup and the workspace in every new shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "source /underlay_ws/install/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

# Set up the firmware workspace
WORKDIR /ros2_ws
RUN mkdir -p src

# setup python .venv for the webUI
RUN python3 -m venv /ros2_ws/.venv && \
    /ros2_ws/.venv/bin/pip install --upgrade pip && \
    /ros2_ws/.venv/bin/pip install fastapi uvicorn jinja2 pyftdi PyYAML numpy

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

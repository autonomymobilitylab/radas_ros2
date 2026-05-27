FROM osrf/ros:jazzy-desktop

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    python3-venv \
    python3-git \
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
    ros-jazzy-diagnostic-updater \
    ros-jazzy-pcl-ros \
    ros-jazzy-nmea-msgs \
    ros-jazzy-rtcm-msgs \
    ros-jazzy-camera-info-manager \
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

# Clone Pylon
RUN git clone https://github.com/basler/pylon-ros-camera.git src/pylon-ros2-camera

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

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

#!/bin/bash

defult_iname="rolimoa-release:ubuntu22.04"

if [ -n "$BUILD" ]; then
    if [ "$BUILD" = "DEBUG" ]; then
        defult_iname="rolimoa:ubuntu22.04"
    fi
fi

iname=${DOCKER_IMAGE:-${defult_iname}} ##
cname=${DOCKER_CONTAINER:-"rolimoa"} ## name of container (should be same as in exec.sh)

DEFAULT_USER_DIR="$(pwd)"
DEFAULT_USER_DIR="${DEFAULT_USER_DIR%/*}"
mtdir=${MOUNTED_DIR:-$DEFAULT_USER_DIR}

if [ $# -eq 0 -a -z "$OPT" ]; then
    OPT=-it
fi

if [ -z "$NO_GPU" ]; then
    GPU_OPT='--gpus all,"capabilities=compute,graphics,utility,display"'
else
    GPU_OPT=""
fi
#echo "GPU_OPT: $GPU_OPT"

## --net=mynetworkname
## docker inspect -f '{{.NetworkSettings.Networks.mynetworkname.IPAddress}}' container_name
## docker inspect -f '{{.NetworkSettings.Networks.mynetworkname.Gateway}}'   container_name

NET_OPT="--net=host"
# for gdb
#NET_OPT="--net=host --env=DOCKER_ROS_IP --env=DOCKER_ROS_MASTER_URI --cap-add=SYS_PTRACE --security-opt=seccomp=unconfined"

DOCKER_ENVIRONMENT_VAR=""

if [ -n "$USE_USER" ]; then
    USER_SETTING=" -u $(id -u):$(id -g) -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro"
fi

##xhost +local:root
xhost +si:localuser:root

rmimage=$(docker rm ${cname})


if [ -n "$BUILD" ]; then
    if [ "$BUILD" = "DEBUG" ]; then
        VAR=${@:-"bash"}
        docker run \
            --privileged     \
            ${OPT}           \
            ${GPU_OPT}       \
            ${NET_OPT}       \
            ${USER_SETTING}  \
            ${DOCKER_ENVIRONMENT_VAR} \
            --env="DISPLAY"  \
            --env="QT_X11_NO_MITSHM=1" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
            --name=${cname} \
            --device=/dev:/dev \
            -v ${mtdir}:/userdir \
            -w="/userdir" \
            ${iname} \
            ${VAR}
    fi
    else
        docker run \
            --privileged     \
            ${OPT}           \
            ${GPU_OPT}       \
            ${NET_OPT}       \
            ${USER_SETTING}  \
            ${DOCKER_ENVIRONMENT_VAR} \
            --env="DISPLAY"  \
            --env="QT_X11_NO_MITSHM=1" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
            --name=${cname} \
            --device=/dev:/dev \
            -w="/root/RoLIMOA" \
            ${iname} \
            bash -c "cd /root/RoLIMOA/server && npm i && npm start"
fi



##xhost -local:root

## capabilities
# compute	CUDA / OpenCL アプリケーション
# compat32	32 ビットアプリケーション
# graphics	OpenGL / Vulkan アプリケーション
# utility	nvidia-smi コマンドおよび NVML
# video		Video Codec SDK
# display	X11 ディスプレイに出力
# all
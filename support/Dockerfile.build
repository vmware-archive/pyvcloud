FROM python:3

ARG build_user=root
ARG build_uid=0
ARG build_gid=0

ENV HOME /home/${build_user}

# Creates the build user with the provided UID/GID
# values to prevent filesystem permissions issues
RUN if [ "${build_uid}" != "0" ]; then \
    groupadd -g ${build_gid} ${build_user}; \
    useradd -c "Build user" -d $HOME -u ${build_uid} \
        -g ${build_gid} -m ${build_user}; \
    fi

# Switch to the new build user
USER ${build_user}
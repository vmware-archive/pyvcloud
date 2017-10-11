FROM python:3

WORKDIR /root
RUN pip install --no-cache-dir pyvcloud
CMD ["bash"]

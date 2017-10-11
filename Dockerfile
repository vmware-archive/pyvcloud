FROM python:3

WORKDIR /root
RUN pip install --no-cache-dir vcd-cli
RUN vcd version
CMD ["bash"]

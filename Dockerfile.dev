FROM python:3

WORKDIR /root/vcd-cli
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py develop
RUN vcd version
CMD ["bash"]

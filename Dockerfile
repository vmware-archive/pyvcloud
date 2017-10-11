FROM python:3

WORKDIR /root/pyvcloud
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py develop
CMD ["bash"]

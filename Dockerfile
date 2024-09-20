FROM python:3.10.15-alpine AS base

# Install ffmpeg
RUN apk update&& \
    apk add ffmpeg

WORKDIR /kuku-dl

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "kuku.py"]

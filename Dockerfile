FROM python:3.13-slim

RUN mkdir home/app
WORKDIR /home/app

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --upgrade pip 
COPY requirements.txt  /home/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /home/app/

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--preload", "RedditCommentStream.wsgi:application"]
FROM mcr.microsoft.com/playwright:focal

RUN apt-get update && apt-get -y install x11vnc websockify novnc python3 python3-pip

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install playwright
RUN playwright install

COPY . .

ARG APP_VERSION
ARG DEPLOYMENT_TIME
ARG COMMIT_MESSAGE
ENV APP_VERSION=$APP_VERSION
ENV DEPLOYMENT_TIME=$DEPLOYMENT_TIME
ENV COMMIT_MESSAGE=$COMMIT_MESSAGE

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

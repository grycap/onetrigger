FROM bitnami/minideb:stretch as builder
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /onetrigger
COPY onetrigger onetrigger
COPY requirements.txt .
RUN pip3 install -r requirements.txt \
 && pip3 install pyinstaller
RUN pyinstaller --onefile onetrigger/onetrigger.py


FROM bitnami/minideb:stretch
RUN addgroup --system app \
 && adduser --system --ingroup app app
WORKDIR /home/app
COPY --from=builder /onetrigger/dist/onetrigger .
RUN chown -R app:app ./
USER app
CMD ["./onetrigger", "run"]
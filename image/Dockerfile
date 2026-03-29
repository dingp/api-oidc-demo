FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m venv "$VIRTUAL_ENV"
COPY app/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app/n10_api_oidc_demo ./n10_api_oidc_demo
COPY app/templates ./templates

EXPOSE 8000

CMD ["uvicorn", "n10_api_oidc_demo.main:app", "--host", "0.0.0.0", "--port", "8000"]

# KURUL Search API — Hugging Face Spaces (Docker SDK)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kulliyati public GitHub deposundan cek (kimlik dogrulama gerekmez).
# Kulliyat guncellendiginde Space'i yeniden build etmek yeterli.
RUN git clone --depth 1 https://github.com/akifkusaslan/kurul.git /data \
    && rm -rf /data/.git /data/api

COPY *.py ./

ENV KURUL_VERI_DIZINI=/data
ENV PYTHONUNBUFFERED=1
EXPOSE 7860

# KURUL_API_KEY, Space'in Secrets bolumunden gelir. Kodda ve depoda YOKTUR.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

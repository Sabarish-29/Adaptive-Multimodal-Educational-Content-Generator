FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Debug: show snippet of main.py before copy (should not exist yet)
RUN echo '--- pre-copy listing ---' && ls -R . || true
COPY . .
RUN echo '--- post-copy main.py head ---' && sed -n '1,140p' contentgen/main.py && \
	echo '--- grep parents[3] (should be empty) ---' && grep -n "parents\[3\]" contentgen/main.py || echo 'no legacy parents index'
EXPOSE 8003
CMD ["uvicorn", "app_boot:app", "--host", "0.0.0.0", "--port", "8003"]

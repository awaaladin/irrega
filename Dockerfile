FROM node:22-slim AS assets
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tailwind.config.js ./
COPY scripts ./scripts
COPY static ./static
COPY templates ./templates
COPY apps ./apps
RUN npm run vendor && npm run build:css

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=assets /app/static/css ./static/css
COPY --from=assets /app/static/vendor ./static/vendor
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]

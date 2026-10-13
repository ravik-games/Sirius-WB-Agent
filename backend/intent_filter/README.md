Сервис по определению фильтрации релевантности запроса пользователя и декопозиции запроса на отдельные товары.

Чтобы запустить сервис:

# 1. Build Docker image

```
docker build -t intent-filter .
```

# 2. Run container

```
docker run --rm -p 8001:8001 intent-filter
```

Метрики модели:


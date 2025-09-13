# Татарский язык - API для изучения

## Описание
Flask API для изучения татарского языка с использованием MongoDB. Пользователи регистрируются без почты и пароля, получают UUID и токен для доступа.

## Функции
- Регистрация пользователей (UUID + токен)
- Получение карточек с татарскими словами и переводами
- Отправка ответов на карточки
- Статистика пользователей
- Рейтинг по количеству изученных слов
- Рейтинг по максимальному стрику

## Установка

1. Установите зависимости:
\\\ash
pip install -r requirements.txt
\\\

2. Убедитесь, что MongoDB запущен на localhost:27017

3. Запустите приложение:
\\\ash
python app.py
\\\

## API Endpoints

### POST /register
Регистрация нового пользователя
\\\json
{
  \
success\: true,
  \user_id\: \uuid\,
  \token\: \uuid\
}
\\\

### GET /cards
Получение всех карточек
\\\json
{
  \success\: true,
  \cards\: [
    {
      \card_id\: \uuid\,
      \tatar_word\: \сәлам\,
      \russian_translation\: \привет\,
      \difficulty\: \easy\
    }
  ]
}
\\\

### POST /answer
Отправка ответа
\\\json
{
  \user_id\: \uuid\,
  \token\: \uuid\,
  \card_id\: \uuid\,
  \is_correct\: true
}
\\\

### GET /rating/words
Рейтинг по количеству изученных слов

### GET /rating/streak
Рейтинг по максимальному стрику

### GET /stats/<user_id>
Статистика пользователя

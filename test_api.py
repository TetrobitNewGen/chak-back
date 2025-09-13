import requests
import json

BASE_URL = 'http://localhost:5000'

def test_api():
    print('=== Тестирование API для изучения татарского языка ===\n')
    
    # 1. Регистрация пользователя
    print('1. Регистрация пользователя...')
    register_response = requests.post(f'{BASE_URL}/register')
    if register_response.status_code == 200:
        user_data = register_response.json()
        user_id = user_data['user_id']
        token = user_data['token']
        print(f'✅ Пользователь зарегистрирован: {user_id}')
        print(f'Токен: {token}\n')
    else:
        print('❌ Ошибка регистрации')
        return
    
    # 2. Получение карточек
    print('2. Получение карточек...')
    cards_response = requests.get(f'{BASE_URL}/cards')
    if cards_response.status_code == 200:
        cards_data = cards_response.json()
        cards = cards_data['cards']
        print(f'✅ Получено карточек: {len(cards)}')
        for i, card in enumerate(cards[:3], 1):
            print(f'  {i}. {card[\
tatar_word\]} - {card[\russian_translation\]}')
        print()
    else:
        print('❌ Ошибка получения карточек')
        return
    
    # 3. Отправка ответов
    print('3. Отправка ответов...')
    if cards:
        # Правильный ответ
        answer_data = {
            'user_id': user_id,
            'token': token,
            'card_id': cards[0]['card_id'],
            'is_correct': True
        }
        answer_response = requests.post(f'{BASE_URL}/answer', json=answer_data)
        if answer_response.status_code == 200:
            print('✅ Правильный ответ отправлен')
        
        # Неправильный ответ
        answer_data['is_correct'] = False
        answer_data['card_id'] = cards[1]['card_id']
        answer_response = requests.post(f'{BASE_URL}/answer', json=answer_data)
        if answer_response.status_code == 200:
            print('✅ Неправильный ответ отправлен')
        print()
    
    # 4. Получение статистики пользователя
    print('4. Статистика пользователя...')
    stats_response = requests.get(f'{BASE_URL}/stats/{user_id}')
    if stats_response.status_code == 200:
        stats = stats_response.json()['stats']
        print(f'✅ Статистика:')
        print(f'  Всего вопросов: {stats[\total_questions\]}')
        print(f'  Правильных ответов: {stats[\correct_answers\]}')
        print(f'  Текущий стрик: {stats[\current_streak\]}')
        print(f'  Максимальный стрик: {stats[\max_streak\]}')
        print()
    
    # 5. Получение рейтинга
    print('5. Рейтинг по словам...')
    words_rating = requests.get(f'{BASE_URL}/rating/words')
    if words_rating.status_code == 200:
        rating_data = words_rating.json()
        print(f'✅ Рейтинг по словам получен: {len(rating_data[\rating\])} пользователей')
        print()
    
    print('6. Рейтинг по стрику...')
    streak_rating = requests.get(f'{BASE_URL}/rating/streak')
    if streak_rating.status_code == 200:
        rating_data = streak_rating.json()
        print(f'✅ Рейтинг по стрику получен: {len(rating_data[\rating\])} пользователей')
        print()
    
    print('=== Тестирование завершено ===')

if __name__ == '__main__':
    test_api()

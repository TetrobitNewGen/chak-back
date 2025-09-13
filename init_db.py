import pymongo
import uuid

# Подключение к MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['tatar_learning']
cards_collection = db['cards']

# Дополнительные карточки для изучения татарского языка
additional_cards = [
    # Базовые слова
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'су', 'russian_translation': 'вода', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'аш', 'russian_translation': 'еда', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'ат', 'russian_translation': 'лошадь', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'эт', 'russian_translation': 'собака', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'мәче', 'russian_translation': 'кошка', 'difficulty': 'easy'},
    
    # Семья
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'ата', 'russian_translation': 'отец', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'әни', 'russian_translation': 'мать', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'бала', 'russian_translation': 'ребенок', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'эне', 'russian_translation': 'младший брат/сестра', 'difficulty': 'medium'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'абы', 'russian_translation': 'старший брат/сестра', 'difficulty': 'medium'},
    
    # Цвета
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'ак', 'russian_translation': 'белый', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'кара', 'russian_translation': 'черный', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'кызыл', 'russian_translation': 'красный', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'яшел', 'russian_translation': 'зеленый', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'зәңгәр', 'russian_translation': 'синий', 'difficulty': 'medium'},
    
    # Числа
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'бер', 'russian_translation': 'один', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'ике', 'russian_translation': 'два', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'өч', 'russian_translation': 'три', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'дүрт', 'russian_translation': 'четыре', 'difficulty': 'easy'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'биш', 'russian_translation': 'пять', 'difficulty': 'easy'},
    
    # Сложные слова
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'ялгызлык', 'russian_translation': 'одиночество', 'difficulty': 'hard'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'дуслык', 'russian_translation': 'дружба', 'difficulty': 'medium'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'хөрмәт', 'russian_translation': 'уважение', 'difficulty': 'hard'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'мәхәббәт', 'russian_translation': 'любовь', 'difficulty': 'medium'},
    {'card_id': str(uuid.uuid4()), 'tatar_word': 'хәтер', 'russian_translation': 'память', 'difficulty': 'hard'}
]

# Добавление карточек в базу данных
if cards_collection.count_documents({}) == 0:
    cards_collection.insert_many(additional_cards)
    print(f'Добавлено {len(additional_cards)} карточек в базу данных!')
else:
    print('Карточки уже существуют в базе данных.')

print('Инициализация базы данных завершена!')

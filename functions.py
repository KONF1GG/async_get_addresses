import re
import requests
from data import BD_AUTHORIZATION
from DataBase import Session, Address, AddedAddresses
from geopy.geocoders import Nominatim
import json
from bs4 import BeautifulSoup

# Функция для получения координат по адресу с сайта OpenStreetMap
def get_location(address):
    geolocator = Nominatim(user_agent='MyGeaopyUA')
    try:
        location = geolocator.geocode(address)
    except Exception as e:
        print(e)
        location = None
    if location:
        if location.raw.get('class') == 'building':
            return location.latitude, location.longitude
        else:
            print('It is not a building')
            return None
    else:
        print('location is empty on NominAPI')
        return None

# Функция для обработки адресов
def clean_address(address):
    shortcuts = ['дом', 'респ', 'край', 'обл', 'гфз', 'аобл', 'аокр', 'мр-н', 'го', 'гп', 'сп', 'внр-н', 'внтерг', 'пос', 'р-н', 'с/с', 'г', 'пгт', 'рп', 'кп', 'гп', 'п', 'аал', 'арбан', 'аул',
    'в-ки', 'г-к', 'з-ка', 'п-к', 'киш', 'п_ст', 'п_ж/д_ст', 'ж/д_бл-ст', 'ж/д_б-ка', 'ж/д_в-ка', 'ж/д_к-ма', 'ж/д_к-т', 'ж/д_пл-ма', 'ж/д_пл-ка', 'ж/д_пп', 'ж/д_оп', 
    'ж/д_рзд', 'ж/д_ст', 'м-ко', 'д', 'с', 'сл', 'ст-ца', 'ст', 'у', 'х', 'рзд', 'зим', 'б-г', 'вал', 'ж/р', 'зона', 'кв-л', 'мкр', 'ост-в', 'парк', 'платф', 'п/р', 'р-н', 
    'сад', 'сквер', 'тер', 'тер.', 'тер_СНО', 'тер_ОНО', 'тер_ДНО', 'тер_СНТ', 'тер_ОНТ', 'тер_ДНТ', 'тер_СПК', 'тер_ОПК', 'тер_ДПК', 'тер_СНП', 'тер_ОНП', 'тер_ДНП', 'тер_ТСН',
    'тер_ГСК', 'ус', 'терфх', 'ю', 'ал', 'б-р', 'взв', 'взд', 'дор', 'ззд', 'км', 'к-цо', 'коса', 'лн', 'мгстр', 'наб', 'пер-д', 'пер', 'пл-ка', 'пл', 'пр-д', 'пр-к', 
    'пр-ка', 'пр-лок', 'пр-кт', 'проул', 'рзд', 'ряд', 'с-р', 'с-к', 'сзд', 'тракт', 'туп', 'ш', 'влд', 'г-ж', 'д', 'двлд', 'зд', 'з/у', 'кв', 'ком', 'подв', 'кот', 
    'п-б', 'к', 'ОНС', 'офис', 'пав', 'помещ', 'рабуч', 'скл', 'coop', 'стр', 'торгзал', 'цех'
]

    # Объединяем сокращения в одно регулярное выражение
    shortcuts_regex = r'\b(?:' + '|'.join(map(re.escape, shortcuts)) + r')\b'

    # Удаляем сокращения из адреса
    address = re.sub(shortcuts_regex, '', address)
    
    return address

#Функция для проверки правильности найденного дома
def check_address_correct(address, house_number):
    house_number = re.sub(r'[\\]', '', house_number)
    cleaned_house_number = re.sub(r'[\\/]', '', house_number)
    if house_number == address.split()[-1] or cleaned_house_number == address.split()[-1]:
        return True
    else:
        return False
    
#Функция для заполнения БД координатами
def post_coordinates(uuid, latitude, longitude):
    # test bd
    # url = 'http://dev1c.freedom1.ru/UNF_TEST_WS2/hs/apps/setHomeCoordinates'
    # main bd
    url = 'http://server1c.freedom1.ru/UNF_CRM_WS/hs/apps/setHomeCoordinates'
    headers = {
        'Authorization': BD_AUTHORIZATION,
        'Content-Type': 'application/json'
    }
    
    data = {
        "UUID": uuid,
        "latitude": latitude,
        "longitude": longitude
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Координаты успешно отправлены!")
    else:
        print(f"Ошибка при отправке координат: {response.status_code} - {response.text}")

# Изменяем адрес для поиска: К примеру в базе адрес :СНТ Строитель 2 n3, 64" - для Яндекса нужно сделать "СНТ Строитель-3, 64"
def modify_address_for_Yandex(address):
    if 'сад' in address:
        address = address.replace('сад', '')

    address = address.replace('  ', ' ')

    address = re.sub(r'(?<=\d) n | n(?=\d)', '-', address)
    address = re.sub(r'\d-(?=\d)', '', address)
    return address.strip()

# Функция для запоминания адресов которые не смог найти парсер
def add_address_without_location_in_DB(house_id, address):
    session = Session()

    try:
        new_address = Address(
            house_id=house_id,
            address=address,
            search_service=['Nominatium (OpenStreetMap)', 'YandexMap']
        )

        session.add(new_address)
        session.commit()

        print(f"Адрес '{address}' с house_id {house_id} был добавлен с ID {new_address.id} in badAddresses")

    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении адреса: {e}")

    finally:
        session.close()

# Функция для проверки, если этот адрес не нашел парсер в прошлом
def check_if_house_in_bad_bd(house_id: int) -> bool:
    session = Session()
    try:
        exists = session.query(Address).filter_by(house_id=house_id).first() is not None

        return exists

    except Exception as e:
        print(f"Ошибка при проверке наличия дома: {e}")
        return False

    finally:
        session.close()
# Функция для проверки, что этот адрес уже был проверен
def check_if_address_in_bd(house_id: int) -> bool:
    session = Session()
    try:
        exists = session.query(AddedAddresses).filter_by(house_id=house_id).first() is not None
        return exists

    except Exception as e:
        print(f"Ошибка при проверке наличия дома: {e}")
        return False

    finally:
        session.close()

# Функция для запоминания адреса, который успешно удалось найти
def post_address_in_bd(house_id, address, location):
    session = Session()

    try:
        new_address = AddedAddresses(
            house_id=house_id,
            address=address,
            location=location
        )

        session.add(new_address)
        session.commit()

        print(f"Адрес '{address}' с house_id {house_id} был добавлен с ID {new_address.id} in addedAdderesses")

    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении адреса: {e}")

    finally:
        session.close()


def get_settlements():
    settles_url = 'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds%20%27@searchType:{settlement}%27%20Limit%200%202000&pretty=1'
    settlement_name = []
    response_settle = requests.get(settles_url)
    if response_settle.status_code == 200:
        try:
            soup_settle = BeautifulSoup(response_settle.text, 'html.parser')
            pre_tag_settle = soup_settle.find('pre')
            if pre_tag_settle:
                json_text_settle = pre_tag_settle.text
                data_settle = json.loads(json_text_settle)

                if not data_settle:
                    print("No data returned from the server (settle).")
                else:
                    for (key, value) in data_settle.items():
                        if value.get('addressShort').split()[0].lower() not in settlement_name:
                            settlement_name.append(value.get('addressShort').split()[0].lower())
        except Exception as e:
            print(e)

        return settlement_name

print(get_settlements())

def get_cities():
    city_url = 'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds%20%27@searchType:{city}%27%20Limit%200%202000&pretty=1'
    cities_name = []
    response_city = requests.get(city_url)
    if response_city.status_code == 200:
        try:
            soup_city = BeautifulSoup(response_city.text, 'html.parser')
            pre_tag_city = soup_city.find('pre')
            if pre_tag_city:
                json_text_city = pre_tag_city.text
                data_city = json.loads(json_text_city)

                if not data_city:
                    print("No data returned from the server (settle).")
                else:
                    for (key, value) in data_city.items():
                        if value.get('addressShort').split()[0].lower() not in cities_name:
                            cities_name.append(value.get('addressShort').split()[0].lower())
        except Exception as e:
            print(e)

        return cities_name

def get_areas(area):
    session = Session()
    area = '%' + area + '%'
    try:
        results = session.query(AddedAddresses).filter(AddedAddresses.address.like(area)).all()
        return results

    except Exception as e:
        print(f"Ошибка при проверке наличия дома: {e}")
        return False

    finally:
        session.close()

def get_coord_of_areas(area):
    ...

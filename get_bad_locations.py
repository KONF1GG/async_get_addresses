import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm
import functions
from DataBase import AddedAddresses, Session
from Yandex_map_parser import YandexMapParser
import time
import csv


parser = YandexMapParser()
time.sleep(5)
async def fetch(session, url):
    async with session.get(url) as response:
        response_text = await response.text()
        return response_text


async def get_settlements():
    settles_url = 'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds%20%27@searchType:{settlement}%27%20Limit%200%202000&pretty=1'
    settlement_name = []

    async with aiohttp.ClientSession() as session:
        response_text = await fetch(session, settles_url)
        try:
            soup_settle = BeautifulSoup(response_text, 'html.parser')
            pre_tag_settle = soup_settle.find('pre')
            if pre_tag_settle:
                json_text_settle = pre_tag_settle.text
                data_settle = json.loads(json_text_settle)
                if not data_settle:
                    print("No data returned from the server (settle).")
                else:
                    for key, value in data_settle.items():
                        if value.get('addressShort').split()[0].lower() not in settlement_name:
                            settlement_name.append(value.get('addressShort').split()[0].lower())
        except Exception as e:
            print(e)
        return settlement_name


async def get_cities():
    city_url = 'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds%20%27@searchType:{city}%27%20Limit%200%202000&pretty=1'
    cities_name = []

    async with aiohttp.ClientSession() as session:
        response_text = await fetch(session, city_url)
        try:
            soup_city = BeautifulSoup(response_text, 'html.parser')
            pre_tag_city = soup_city.find('pre')
            if pre_tag_city:
                json_text_city = pre_tag_city.text
                data_city = json.loads(json_text_city)
                if not data_city:
                    print("No data returned from the server (city).")
                else:
                    for key, value in data_city.items():
                        if value.get('addressShort').split()[0].lower() not in cities_name:
                            cities_name.append(value.get('addressShort').split()[0].lower())
        except Exception as e:
            print(e)
        return cities_name


async def process_settlement(session, setl, limit_start):
    limit_ = '10000'
    url_all = f'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds:geo%20%27%20@searchType:%7Bhouse%7D%20@searchTitle:{setl}%27%20Limit%20{limit_start}%20{limit_}&pretty=1'
    # url = f'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds:geo%20%27%20@searchType:%7Bhouse%7D%20@searchTitle:{setl}%20-@latitude:[0%2090]%27%20Limit%20{limit_start}%20{limit_}&pretty=1'
    response_text = await fetch(session, url_all)
    try:
        soup = BeautifulSoup(response_text, 'html.parser')
        pre_tag = soup.find('pre')
        if pre_tag:
            json_text = pre_tag.text
            data = json.loads(json_text)
            if not data:
                return []  # Возвращаем пустой список, если нет данных
            else:
                # Преобразуем данные в список домов
                return data
    except Exception as e:
        print(e)
    return []  # Возвращаем пустой список, если возникла ошибка



list_of_areas = []
async def main():
    # setl_list = await get_settlements()
    # cities_list = await get_cities()
    # list_of_all = list(set(setl_list + cities_list))
    #
    # total_count = 0
    #
    # # list_of_all = ['краснодар']
    # async with aiohttp.ClientSession() as session:
    #     for setl in tqdm(list_of_all):
    #         tasks = []
    #         for limit_start in ['0', '10000', '20000', '30000', '40000', '50000', '60000', '70000', '80000', '90000',
    #                             '100000']:
    #             task = asyncio.create_task(process_settlement(session, setl, limit_start))
    #             tasks.append(task)
    #
    #         results = await asyncio.gather(*tasks)
    #
    #         # Проверяем, получили ли мы данные
    #         for result in results:
    #             if result:
    #                 for house_id, value in result.items():
    #                     title = value.get('searchTitle')
    #                     modify_title = ', '.join(functions.modify_address_for_Yandex(functions.clean_address(title)).split(', ')[:3])
    #                     if modify_title not in list_of_areas:
    #                         list_of_areas.append(modify_title)
    #             else:
    #                 continue
    #
    # # Записываем list_of_areas в текстовый файл
    # with open('list_of_areas.txt', 'w', encoding='utf-8') as file:
    #     for area in list_of_areas:
    #         file.write(f"{area}\n")


    with open('list_of_areas.txt', 'r', encoding='utf-8') as file:
        for line in file:
            list_of_areas.append(line.strip())

    unique_coordinates = {}
    for i, area in tqdm(enumerate(list_of_areas[130:])):
        coordinates = parser.get_location_from_Yandex(area)
        if coordinates:
            lat = coordinates.get('latitude')
            lon = coordinates.get('longitude')
            if lat and lon:  # Ensure coordinates are not None or empty
                try:
                    # Convert to float if they are not already
                    lat = float(lat)
                    lon = float(lon)
                    unique_coordinates[area] = {'latitude': lat, 'longitude': lon}
                except ValueError:
                    print(f"Invalid coordinate value for area: {area}")

    # Write coordinates to CSV
    with open('coordinates.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['area', 'latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for area, coord in unique_coordinates.items():
            writer.writerow({'area': area, 'latitude': coord.get('latitude'), 'longitude': coord.get('longitude')})

if __name__ == '__main__':
    asyncio.run(main())

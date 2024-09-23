import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm


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
    url = f'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds:geo%20%27%20@searchType:%7Bhouse%7D%20@searchTitle:{setl}%27%20Limit%20{limit_start}%20{limit_}&pretty=1'
    # url = f'https://ws.freedom1.ru/redis/raw?query=FT.SEARCH%20idx:adds:geo%20%27%20@searchType:%7Bhouse%7D%20@searchTitle:{setl}%20-@latitude:[0%2090]%27%20Limit%20{limit_start}%20{limit_}&pretty=1'
    response_text = await fetch(session, url)
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

async def main():
    setl_list = await get_settlements()
    cities_list = await get_cities()
    list_of_all = list(set(setl_list))

    total_count = 0

    # list_of_all = ['северский']
    async with aiohttp.ClientSession() as session:
        for setl in tqdm(list_of_all):
            tasks = []
            for limit_start in ['0', '10000', '20000', '30000', '40000', '50000', '60000', '70000', '80000', '90000', '100000', '110000']:
                task = asyncio.create_task(process_settlement(session, setl, limit_start))
                tasks.append(task)
                
            results = await asyncio.gather(*tasks)
            
            # Проверяем, получили ли мы данные
            for result in results:
                if result:
                    for house in result:
                        # if house == 'adds:493338':
                        #     print(result['adds:493338'])
                        # print(house)
                        total_count += 1
                else:
                    continue
    
    cities_list = await get_cities()
    print(f"Total number of houses: {total_count}")

if __name__ == '__main__':
    asyncio.run(main())

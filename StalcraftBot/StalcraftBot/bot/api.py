import os 
import aiohttp
import asyncio
from dotenv import load_dotenv
from config import LIST_ITEMS

# Получение api-ключа
load_dotenv()
API_KEY = os.getenv('API_KEY')

# api для подключения к аукциону 
class ApiAuction:

    # Инициализация
    def __init__(self, item):
        self.total = 0
        self.item = item
        self.token = API_KEY
        self.DISCOUNT = 0.99
        self._url = f'https://eapi.stalcraft.net/ru/auction/{self.item}/lots'
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}

    # Получение лотов предмета с аукциона
    async def _relevant_lots(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self._url, headers=self.headers) as response:
                response_data = await response.json()
                self.total = response_data['total']
                return response_data.get('lots')

    # Разеделние лотов на 'Количество':'Цена'
    async def _relevant_price_of_lots(self) -> list[str]:
        data = await self._relevant_lots()
        return [f"{lot['amount']} : {lot['buyoutPrice']}" for lot in data]

    # Получение цены за предмет в одном экземпляре 
    def _calculate_price_per_item(self, price_str) -> int:
        amount, buyout_price = map(int, price_str.split(':'))
        if amount == 0:
            raise ValueError('Делить на 0 нельзя')
        return buyout_price / amount

    # Поиск подходящих лотов
    def _find_profit_lots(self, data_price, average_price, task):
        result_list = []

        def add_result(quantity, price, average_price, unit_price):
            result_list.append(f'{quantity}:{price}:{round((unit_price / average_price), 2)}')

        for item in data_price:
            quantity, price = map(int, item.split(':'))

            if price == 0: continue
            unit_price = price / quantity
            if unit_price < (average_price * self.DISCOUNT): 
                add_result(quantity, price, average_price, unit_price)

        if result_list:
            result_list.sort(key=lambda lot: float(lot.split(':')[-1]))
            return {
                'lots': result_list[0:1], 
                'item': LIST_ITEMS[task],
                'total': self.total,
                'average_price': average_price, 
            }

        return 
        
    # 
    async def get_response(self, task) -> dict[str:list, str:str, str:int, str:int]:
        data_price = await self._relevant_price_of_lots() 
        one_item_price = [self._calculate_price_per_item(price) for price in data_price]
        average_price = int(sum(one_item_price) / len(one_item_price))
        filtered_prices = [price for price in one_item_price if price <= average_price * 1.7]
        filtered_average_price = int(sum(filtered_prices) / len(filtered_prices)) 
        data = self._find_profit_lots(data_price, filtered_average_price, task)
        return data


async def get_work():
    items = LIST_ITEMS  
    tasks = [] # Список для хранения задач

    for item in items:
        item_target = ApiAuction(item)
        tasks.append(item_target.get_response(item)) 

    # Запускаем все задачи параллельно и ждем их завершения
    responses = await asyncio.gather(*tasks)
    data = [response for response in responses if response]

    # Расчет прибыли и добавление в словарь
    for item in data:
        potential_profit = (int(item['lots'][0].split(':')[0]) * int(item['average_price'])) - int(item['lots'][0].split(':')[1])
        item['potential_profit'] = potential_profit

    # Сортировка по потенциальной прибыли
    sorted_data = sorted(data, key=lambda x: x['potential_profit'], reverse=True)

    # Вывод отсортированных данных
    return sorted_data


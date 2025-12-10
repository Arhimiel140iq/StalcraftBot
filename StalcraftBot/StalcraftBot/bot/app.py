import math
import time 
import asyncio
import keyboard 
import colorama
from api import get_work
from auction_bot import Bot
from colorama import Fore, Back, init

running = False  

async def main():
    global running
    while running:  
        # try:
        work = await get_work()

        if work:
            print(Fore.LIGHTMAGENTA_EX + f'Количество:Цена:Коефициент -> {work[0]["lots"]}')
            print(Fore.LIGHTCYAN_EX + f'Название предмета: {work[0]["item"]}')
            for task in work[0:3]:
                count_pages = task['total'] / 50
                item = task['item']
                pages = math.ceil(count_pages)

                for elem in task['lots']:
                    values_elem = elem.split(':')
                    quantity = values_elem[0]
                    price = values_elem[1]
                    target = f'{price}:{quantity}'
                    obj_item = Bot(item, pages, target)
                    result = obj_item.start_bot()

                    with open('bot/log_error.txt', 'r', encoding='utf-8') as file_error:
                        lines = file_error.readlines()
                        sample_error, sample_income = lines[0].split(' / '), lines[0].split(' / ')


                        count_error = int(sample_error[0].split(": ")[1]) + 1
                        sample_error[0] = f'Ошибки: {count_error}' 

    
                        current_income = int(float(sample_income[2].split(": ")[1]))
                        income = int(current_income + (int(task['potential_profit']) * 0.95))
                        count_lots = int(sample_error[1].split(": ")[1]) + 1
                        sample_income[2] = f'Потенциальный заработок с сессии: {income}' 
                        sample_income[1] = f'Купленные предметы: {count_lots}'  
                        file_error.close()

                    if result is True:
                        with open('bot/log_lots.txt', 'a', encoding='utf-8') as file_lots:
                            file_lots.write('Name: ' + task['item'] + '\n')
                            file_lots.write('Цена: ' + price + '\n')
                            file_lots.write('Количество: ' + quantity + '\n')
                            file_lots.write('Средняя цена на рынке: ' + str(task['average_price']))
                            file_lots.write('\n')
                            file_lots.write('\n')
                            file_lots.write('\n')

                        
                        with open('bot/log_error.txt', 'r+', encoding='utf-8') as file_error:
                            file_error.truncate(0)
                            file_error.write(' / '.join(sample_income))

                        continue

                    
                    with open('bot/log_error.txt', 'r+', encoding='utf-8') as file_error:
                        file_error.truncate(0)
                        file_error.write(' / '.join(sample_error))
                    continue
        else:
            print(Fore.LIGHTCYAN_EX + '[...searching lots...]')
            await asyncio.sleep(11)  
        # except Exception as e:
        #     print(e)

def start_bot():
    global running
    running = True
    asyncio.run(main())

if __name__ == "__main__":
    keyboard.add_hotkey('F6', start_bot)  

    print("Нажмите F6 для запуска бота")
    keyboard.wait() 


import cv2 
import time
import colorama
import pyautogui
import pyperclip
import pytesseract
import numpy as np
from PIL import ImageGrab
from colorama import Fore, Back, init
from concurrent.futures import ThreadPoolExecutor
from config import (PATH_TO_TESSERACT, DEFAULT_SCROLL_DISTANCE, DEFAULT_SIDEBAR_X, 
                    DEFAULT_SIDEBAR_Y, DEFAULT_PRICES_REGION_COORDINATES, DEFAULT_COUNT_REGION_COORDINATES, LENGTH_TRUE_STRING_AFTER_BUYING, 
                    DEFAULT_SEARCH_FIELD_X, DEFAULT_SEARCH_FIELD_Y, DEFAULT_SEARCH_BUTTON_X, DEFAULT_SEARCH_BUTTON_Y, DEFAULT_SORTING_BUTTON_X, 
                    DEFAULT_SORTING_BUTTON_Y, DEFAULT_CHECKING_REGION_COORDINATES, DELAY_FUNC, DELAY_BOT, DELAY_CLICK, DELAY_DURATION, 
                    BUY_COORDINATES_X, BUY_COORDINATES_Y, SEARCH_BUTTON_AUCTION_X, SEARCH_BUTTON_AUCTION_Y, AUCTION_SCREENSHOT, 
                    DEFAULT_COORDINATES_AVERAGE_PAGE, DEFAULT_PAGE_SWITCH_COORDINATES_Y, MAX_TRY_CORRECTION, THRESHOLDS_COUNT_LOTS, 
                    THRESHOLDS_PRICES_LOTS, DISTANCE_BETWEEN_LOTS)

pytesseract.pytesseract.tesseract_cmd = PATH_TO_TESSERACT
def check_purchase_state(func):
    def wrapper(*args, **kwargs):
        if args[0].state_purchase:
            return
        return func(*args, **kwargs)
    return wrapper

class Bot():
    colorama.init()
    init(autoreset=True) 
    def __init__(self, item, pages, target):
        self.direction = ''
        self.step = 24
        self.left_move = 0
        self.right_move = 1
        self.item = item
        self.pages = pages
        self.target = target
        self.position = 0
        self.correction = 0
        self.check_number = 0 
        self.state_purchase = False
        

    # Открытие аукциона
    def start(self):
        pyautogui.press('p')  
        time.sleep(DELAY_CLICK)
        pyautogui.moveTo(SEARCH_BUTTON_AUCTION_X, SEARCH_BUTTON_AUCTION_Y)
        pyautogui.click(duration=DELAY_CLICK)

        # Выход с аукциона 
    def exit(self):
        pyautogui.press('esc')
    
    # Переключение состояния бота
    def switch_state(self):
        print(Fore.BLACK + Back.LIGHTRED_EX + '[ ЛОТ НЕ НАЙДЕН ]')
        self.state_purchase = True
        return

    # Функция покупки лота
    def click_to_buy(self):
        # Захват скриншота
        screenshot = ImageGrab.grab(bbox=(1010, 383, 1385, 758))
        screenshot.save('bot/screenshots/tempalte_prices.png')
        screenshot = cv2.imread('bot/screenshots/tempalte_prices.png')
        template = cv2.imread('bot/screenshots/template.png')

        # Поиск шаблона
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        template_height, template_width = template.shape[:2]
        threshold = 0.8
        yloc, xloc = np.where(result >= threshold)

        # Если найден хотя бы один объект
        if len(xloc) > 0 and len(yloc) > 0:
            for (x, y) in zip(xloc, yloc):
                cv2.rectangle(screenshot, (x, y), (x + template_width, y + template_height), (0, 255, 0), 2)

                # Вычисляем абсолютные координаты для клика
                absolute_x = x + 1010 
                absolute_y = y + 383   

                # Покупаем
                pyautogui.moveTo(absolute_x + 50, absolute_y + 15)
                pyautogui.click()
                break
        return 

    # Проверка покупки лота
    def checking_purchased_lot(self):
        # Скриншот 
        screenshot = ImageGrab.grab(bbox=DEFAULT_CHECKING_REGION_COORDINATES)
        screenshot.save('bot/screenshots/purchased_str.png')
        text = pytesseract.image_to_string(screenshot)

        # Если в скриншоте есть текст о покупке 
        if len(text) == LENGTH_TRUE_STRING_AFTER_BUYING: 
            self.is_buy = True
            print(Fore.YELLOW + Back.LIGHTGREEN_EX + '{ ЛОТ КУПЛЕН }')
            return True
        
        print(Fore.YELLOW + Back.LIGHTRED_EX + '{ ЛОТ НЕ КУПЛЕН }')
        return False 
    
    # Попытка покупки лота
    def buy_item(self, coords):

        # Завершаем task покупакой лота
        self.state_purchase = True
        pyautogui.moveTo(BUY_COORDINATES_X, (BUY_COORDINATES_Y) + coords)
        pyautogui.click()            
        time.sleep(DELAY_CLICK)
        self.click_to_buy()
        time.sleep(DELAY_CLICK)

        # Проверка покупки лота 
        result = self.checking_purchased_lot()
        pyautogui.moveTo(960, 570) 
        pyautogui.click()             
        time.sleep(DELAY_BOT)

        # Возвращаем результат
        return result

    # Корректировка страницы лотов
    def correction_page_position(self, times):

        # Не более 3 корректировок
        if self.correction > MAX_TRY_CORRECTION: return
        self.correction += 1

        # Высчитываем и прокручиваем на N-нное расстояние вниз
        pyautogui.moveTo(DEFAULT_SIDEBAR_X, DEFAULT_SIDEBAR_Y)
        scroll_length = (10 - int(times)) * DISTANCE_BETWEEN_LOTS 
        pyautogui.mouseDown(duration=DELAY_DURATION)
        pyautogui.move(0, scroll_length, duration=DELAY_DURATION)  
        pyautogui.mouseUp(duration=DELAY_DURATION)
        
    # Переход в начальную позицию поиска
    def get_start_position(self):

        # Сортировка лотов по цене
        pyautogui.moveTo(DEFAULT_SORTING_BUTTON_X, DEFAULT_SORTING_BUTTON_Y)
        pyautogui.click(interval=0.4)
        pyautogui.click(interval=0.4)

        # Если страниц больше 2, то поиск начинается с середины футера страниц
        if self.pages > 2:
            target = 1134 if self.pages % 2 else 1122  # Определяем середину страниц учитывая чётность/нечётность видимых страниц
            pyautogui.moveTo(target, DEFAULT_PAGE_SWITCH_COORDINATES_Y)
            pyautogui.click(interval=DELAY_CLICK)

            middle = (self.pages - 1) // 2  # Определяем число середины страниц 
            self.left_move = middle # Определяем шаги влево
            self.right_move = self.pages - middle - 1 # Определяем шаги вправо (Заведомо больше)

            # Определяем координаты старта поиска
            self.position = target

        else:
            self.position = DEFAULT_COORDINATES_AVERAGE_PAGE

        return 

    # Найти предмет
    def item_output(self):
        pyautogui.moveTo(DEFAULT_SEARCH_FIELD_X, DEFAULT_SEARCH_FIELD_Y) 
        pyautogui.click(duration=DELAY_CLICK)
        pyperclip.copy(self.item)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.moveTo(DEFAULT_SEARCH_BUTTON_X, DEFAULT_SEARCH_BUTTON_Y)
        pyautogui.click(duration=DELAY_CLICK)

    # Скриншот лотов
    def screenshot(self):
        screenshot = ImageGrab.grab(bbox=AUCTION_SCREENSHOT)
        prices_region = screenshot.crop(DEFAULT_PRICES_REGION_COORDINATES)
        count_region = screenshot.crop(DEFAULT_COUNT_REGION_COORDINATES)
        prices_region.save('bot/screenshots/prices_region.png')
        count_region.save('bot/screenshots/count_region.png')

    # Обработка скриншота цен (OCR)
    def screenshot_prices_lots_improvement_process(self): 
        screenshot = cv2.imread('bot/screenshots/prices_region.png')
        screenshot = cv2.resize(screenshot, None, fx=9, fy=9) 
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        _, binary_screenshot = cv2.threshold(gray_screenshot, 140, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_image = cv2.morphologyEx(binary_screenshot, cv2.MORPH_CLOSE, kernel)
        return morph_image

    # Обработка скриншота количества лотов (OCR)   
    def screenshot_count_lots_improvement_process(self): 
        screenshot = cv2.imread('bot/screenshots/count_region.png')
        screenshot = cv2.resize(screenshot, None, fx=9, fy=9) 
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        binary_image = cv2.adaptiveThreshold(gray_screenshot, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = 50000.0  
        max_area = 140000.0  
        filtered_contours = [contour for contour in contours if min_area < cv2.contourArea(contour) < max_area]
        return filtered_contours, screenshot 

    # Считывание обработанного скриншота цен (OCR)
    def tesseract_reading_prices_lots(self):
        screenshot = self.screenshot_prices_lots_improvement_process()
        thresholds = THRESHOLDS_PRICES_LOTS
        
        # Функция для обработки изображения с конкретным порогом
        def process_threshold(threshold):
            _, binary_screenshot = cv2.threshold(screenshot, threshold, 255, cv2.THRESH_BINARY_INV)
            text = pytesseract.image_to_string(binary_screenshot, config='outputbase digits')
            data = pytesseract.image_to_data(binary_screenshot, output_type=pytesseract.Output.DICT)
            return data

        # Параллельная обработка с использованием ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_threshold, thresholds))
        
        # Обработка результатов OCR
        final_rows = []
        for data in results:
            last_y = -1
            tolerance = 5  
            rows = []
            current_row = []

            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  
                    text = data['text'][i].strip()  
                    if text: 
                        x = int(data['left'][i] / 9)
                        y = int(data['top'][i] / 9)
                        w = int(data['width'][i] / 9)
                        h = int(data['height'][i] / 9)
                        
                        if last_y == -1 or (y - last_y) > tolerance:  
                            if current_row: 
                                rows.append(current_row)
                                current_row = []

                        current_row.append({
                            'text': text,
                            'coordinates': (x, y, w, h)
                        })
                        last_y = y
            if current_row:
                rows.append(current_row)

            for row in rows:
                numeric_items = [item for item in row if item['text'].isdigit()]
                if numeric_items: 
                    combined_text = ''.join(item['text'] for item in numeric_items)  
                    final_rows.append({
                        'price': combined_text,
                        'coordinates': (numeric_items[0]['coordinates'][0], numeric_items[0]['coordinates'][1], 
                                        numeric_items[-1]['coordinates'][0] + numeric_items[-1]['coordinates'][2] - numeric_items[0]['coordinates'][0], 
                                        numeric_items[0]['coordinates'][3])  
                    })
    
        return final_rows

    # Параллельная обработка количества предметов в скришноте лота (OCR)
    def process_with_multiple_thresholds_parallel(self, roi, thresholds):
        def process_threshold(threshold):
            gray_screenshot_item = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, binary_image_item = cv2.threshold(gray_screenshot_item, threshold, 255, cv2.THRESH_BINARY)
            text = pytesseract.image_to_string(
                binary_image_item, 
                config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
            )
            return text.strip()
        
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_threshold, thresholds))

        return results

    # Считывание обработанного скриншота лотов (OCR)
    def tesseract_reading_count_lots(self):
        filtered_contours, screenshot = self.screenshot_count_lots_improvement_process()
        results = [] 
        thresholds = THRESHOLDS_COUNT_LOTS
        for contour in filtered_contours:
            x, y, w, h = cv2.boundingRect(contour)
            roi = screenshot[y:y+h, x:x+w] 
            ocr_results = self.process_with_multiple_thresholds_parallel(roi, thresholds)
            valid_result = max((result for result in ocr_results if result), key=len, default="1") 
            results.append(valid_result)

        results.reverse()
        return results

    # Параллельный запуск функций OCR
    def pool_executor_OCR(self):
        self.screenshot()
        with ThreadPoolExecutor() as executor:
            future_quantities = executor.submit(self.tesseract_reading_count_lots)
            future_lots = executor.submit(self.tesseract_reading_prices_lots)
            
            quantities = future_quantities.result()
            lots = future_lots.result()
        
        for i in range(len(lots)):
            if i < len(quantities): 
                lots[i]['quantity'] = quantities[i]
        
        return lots

    # Анализ скришонта
    @check_purchase_state
    def OCR_analysis(self): # -> '50000:1'
        result_search = self.pool_executor_OCR() # Паралелльные обработки скриншотов
        review_search = [f"{item['price']}:{item.get('quantity', '1')}" for item in result_search] or ["0:0"]# -> ['50000:1', '40000:2', ...] 

        # Если минимальная цена в скриншоте больше цели, то меняем страницу 
        prices_list = [int(value.split(':')[0]) for value in review_search] or [0]
        if int(self.target.split(':')[0]) < int(min(prices_list)): 
            self.switch_page(prices_list)

        # Если на первой странице есть лоты без цены выкупа, то проматываем их 
        if len(prices_list) < 40 and self.left_move <= -1 and self.correction < MAX_TRY_CORRECTION:
            self.correction_page_position(round(len(prices_list) / 4))
            self.OCR_search()
    
        # Если цель есть в скриншоте
        if self.target in review_search and not self.state_purchase:
            print(Fore.YELLOW + Back.LIGHTYELLOW_EX + '{ ЛОТ НАЙДЕН }')
            index = review_search.index(self.target)
            item_elements = review_search[index].split(':')[0]
            coordinates = max([item['coordinates'] for item in result_search if item['price'] == item_elements])

            # Попытка покупки и завершение работы 
            result = self.buy_item(coordinates[1])
            return result
        
        # Если лот не найден
        print(Fore.LIGHTYELLOW_EX + '[...next iteration...]')
        return review_search

    # Переключение страниц 
    @check_purchase_state
    def switch_page(self, data_price):
        print(Fore.LIGHTWHITE_EX + '[...switch page...]')
        target_price = int(self.target.split(':')[0])
        min_price, max_price = (min(data_price), max(data_price)) if data_price else (0, 0)
        direction = 'left' if int(target_price) < int(min_price) else 'right' 

        # Определяем направление переключение страниц
        if target_price < min_price:
            self.left_move -= 1
        elif target_price > max_price:
            self.right_move -= 1

        # Если страницы закончились
        if self.direction in ['left', 'right'] and direction != self.direction or self.right_move < 0 or self.left_move < 0:
            return self.switch_state()
        
        # Если лот уже купили
        self.direction = direction
        moves = {'left': self.left_move, 'right': self.right_move}
        if (moves[direction] < 0 and min_price <= target_price <= max_price) or self.check_number == min_price + max_price:
            return self.switch_state()
        
        # Переключение страницы
        self.check_number = min_price + max_price
        self.position += self.step if direction == 'right' else -self.step
        pyautogui.moveTo(self.position, DEFAULT_PAGE_SWITCH_COORDINATES_Y)
        pyautogui.click(interval=DELAY_CLICK)

        # Запуск поиска
        self.searching()
    
    # Поиск цели на странице
    @check_purchase_state
    def searching(self):

        #Лист для всех лотов на странице 
        lots = []

        #Смена позиции курсора на полосу прокрутки
        pyautogui.moveTo(DEFAULT_SIDEBAR_X, DEFAULT_SIDEBAR_Y)
        
        # Первый результат скриншота на странице 
        first_search = self.OCR_analysis()
        if isinstance(first_search, bool):  
            return first_search
        elif first_search:  
            lots = [*first_search]

        # Прокрутка и поиск на всей странице 
        for _ in range(4):
            if not self.state_purchase:
                
                # Выполнение прокрутки страницы
                pyautogui.mouseDown(duration=DELAY_CLICK)
                pyautogui.move(0, DEFAULT_SCROLL_DISTANCE, duration=DELAY_DURATION)  
                pyautogui.mouseUp(DELAY_CLICK)

                # Получение результатов OCR
                result = self.OCR_analysis()
                if isinstance(result, bool):  
                    print('bool IF')
                    return result
                elif result:  
                    lots.extend(result)

        #Смена страницы
        data_price = [int(value.split(':')[0]) for value in lots] or [0]
        time.sleep(DELAY_FUNC)
        self.switch_page(data_price)
        return 
    
    def start_bot(self):
        self.start() # Открывает аукцион
        self.item_output() # Поиск лотов 
        self.get_start_position() # Поиск начальной позиции
        result = self.searching() # Поиск предмета
        self.exit() # Выход с аукциона
        self.state_purchase = False
        print(Fore.LIGHTCYAN_EX + "[...next task...]")
        return result




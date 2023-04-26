import pyautogui, cv2, os, json, shutil, win32api, re
from time import sleep
import numpy as np
from win32con import *
import pytesseract as tess
from PIL import Image
import keyboard
import requests

tess.pytesseract.tesseract_cmd = r"C:\Users\Lucas\AppData\Local\Programs\Tesseract-OCR\tesseract"

haggle = {}
ninja_values = {}
league = 'Crucible'

def load_config():
    #Loads all images
    try:
        # Image loading
        image_path = './images'
        config_path = './config'

        haggle['images'] = {}
        for folder in os.listdir(image_path):
            folder_path = f'{image_path}/{folder}'
            haggle['images'][folder] = {}
            for file in os.listdir(folder_path):
                file_name = file.split('.')[0]
                haggle['images'][folder][file_name] = cv2.imread(f'{folder_path}/{file}')

        # Currency loading
        haggle['config'] = {}
        for file in os.listdir(config_path):
            file_name = file.split('.')[0]

            with open(f'{config_path}/{file}') as f:
                haggle['config'] = json.load(f)

    except:
        print("Loading error...")

def click(x, y):
    win32api.SetCursorPos((x,y))
    sleep(0.3)
    win32api.mouse_event(MOUSEEVENTF_LEFTDOWN,0,0)
    win32api.mouse_event(MOUSEEVENTF_LEFTUP,0,0)    

def scroll_in_right(region):
    sleep(0.1)
    while pyautogui.locateOnScreen(haggle['images']['haggle']['right_haggle'], region=region, grayscale=False, confidence=0.95) == None:
        win32api.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -120, 0)
        sleep(0.02)

def start_haggle(name, pos):
    click(pos[0], pos[1])
    sleep(1.5)

    pyautogui.screenshot('./images/temp/haggle_buy.png', region=haggle['config']['positions']['haggle_buy'])
    artifact = find_artifact()

    amount = get_amount()
    
    currency_final_value = round(haggle['config']['currency'][name] * amount, 2)

    min_worth = haggle['config']['artifact'][artifact]

    
    print(f'Found {amount}x {name} = {currency_final_value} for {artifact} artifacts (min value = {min_worth})')

    if currency_final_value >= min_worth:
        buttons = haggle['images']['haggle']
        regions = haggle['config']['positions']
        scroll_in_right(regions['haggle_buy'])
        confirm = pyautogui.locateOnScreen(buttons['confirm'], region=regions['confirm_board'])
        x, y = pyautogui.center(confirm)
        if  confirm != None:
            click(x, y)
        sleep(0.2)
        if pyautogui.locateOnScreen(buttons['wrong_haggle'], region=regions['haggle_buy'], grayscale=False, confidence=0.9) != None:
            sleep(0.2)
            click(x, y)
            sleep(0.3)
        return currency_final_value
    sleep(0.3)
    pyautogui.press("escape")
    click(900, 500)
    return 0

def reroll():
    click(1266, 874)
    sleep(0.2)

def find_currency(name, image, template, hits):
    h, w = template.shape[:2]
    thresh = 0.95

    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    temp_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)


    res = cv2.matchTemplate(image=img_gray, templ=temp_gray, method=cv2.TM_CCORR_NORMED)
    loc = np.where(res >= thresh)

    tree_count = 0
    mask = np.zeros(image.shape[:2], np.uint8)
    for pt in zip(*loc[::-1]):
        if mask[pt[1] + int(round(h/2)), pt[0] + int(round(w/2))] != 255:
            mask[pt[1]:pt[1]+h, pt[0]:pt[0]+w] = 255
            hits[name].append((pt[0] + (w//2), pt[1] + (h//2)))
            cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0,255,0), 1)

def find_artifact():
    image = cv2.imread('./images/temp/haggle_buy.png')

    for art, template in haggle['images']['artifacts'].items():
        if match_artifact(image, template):
            return art

def match_artifact(image, template):
    thresh = 0.9

    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    temp_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(image=img_gray, templ=temp_gray, method=cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= thresh)

    if len(loc[0]) > 0:
        return True

    return False

def get_amount():
    sleep(0.1)
    amount_path = './images/temp/currency_amount.png'
    pyautogui.screenshot(amount_path, region=haggle['config']['positions']['currency_inside_haggle'])

    amount_img = cv2.imread(amount_path)
    hsv = cv2.cvtColor(amount_img, cv2.COLOR_BGR2HSV)

    # define range of white color in HSV
    # change it according to your need !
    lower_white = np.array([0,0,0], dtype=np.uint8)
    upper_white = np.array([0,0,255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_white, upper_white)
    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(amount_img,amount_img, mask= mask)

    cv2.imwrite(amount_path, res)

    img = Image.open(amount_path)
    value = tess.image_to_string(img, config='--psm 6')
    
    if value == '':
        return 1
    return int(re.sub("[^0-9]", "", value))
            
def run(coinages):
    haggle_board = haggle['config']['positions']['haggle_board']
    reroll_value = 3
    
    net_profit = 0
    while coinages >= 1:
        pyautogui.screenshot('./images/temp/board.png', region=haggle_board)

        image = cv2.imread('./images/temp/board.png')

        hits = {}
        currency_path = './images/currency'
        for file in os.listdir(currency_path):
            currency = file.split('.')[0]
            hits[currency] = []
            template = cv2.imread(f'{currency_path}/{file}')
            find_currency(currency, image, template, hits)

        for currency, positions in hits.items():
            if len(positions) > 0:
                print(f'{len(positions)}x hits on {currency}')
                for pos in positions:
                    real_pos = (pos[0] + haggle_board[0], pos[1] + haggle_board[1])
                    net_profit += start_haggle(currency, real_pos)
        coinages -= 1
        if coinages >= 1:
            print("Press Q to reroll")
            while True:
                if keyboard.is_pressed('q'):
                    reroll()
                    net_profit -= reroll_value
                    break                
    print(f"Total gained = {net_profit}c")

def append_worth(entry):
    with open('./config/config.json') as file:
        file_data = json.load(file)

    file_data['currency'].update(entry)
    
    with open('./config/config.json', 'w') as file:
        json.dump(file_data, file, indent=4)
    return 'Done'

def register():
    currency_name = input('Enter currency name in first inventory slot (top, left):')
    pyautogui.screenshot(f'./images/currency/{currency_name}.png', region=haggle['config']['positions']['first_inventory_slot'])

    value = 0
    for k, v in ninja_values.items():
        if currency_name in v:
            value = v[currency_name]
    
    print(append_worth({f"{currency_name}":value}))
        
    cont = int(input('1 - Continuar\n0 - Sair\n'))
    if cont == 1:
        os.system('cls')
        register()

def get_currencies():
    poe_ninja = f'https://poe.ninja/api/data/currencyoverview?league={league}&type=Currency'
    currency_json = requests.get(poe_ninja).json()['lines']
    currency_json = {x['detailsId']:x['chaosEquivalent'] for x in currency_json}
    # test = json.dumps(currency_json, indent=4)
    # with open('currencies.json', 'w') as out:
    #     out.write(test)
    return currency_json

def get_fossils():
    poe_ninja = f'https://poe.ninja/api/data/itemoverview?league={league}&type=Fossil'
    fossil_json = requests.get(poe_ninja).json()['lines']
    fossil_json = {x['detailsId']:x['chaosValue'] for x in fossil_json}
    # test = json.dumps(fossil_json, indent=4)
    # with open('fossils.json', 'w') as out:
    #     out.write(test)
    return fossil_json

def refresh_prices():
    for name, _ in haggle['config']['currency'].items():
        if name != 'chaos-orb':
            if 'fossil' in name:
                haggle['config']['currency'][name] = ninja_values['Fossil'][name]
            else:
                haggle['config']['currency'][name] = ninja_values['Currency'][name]

if "__main__" == __name__:  
    if not os.path.exists('./images/temp'):
        os.makedirs('./images/temp')

    ninja_values['Currency'] = get_currencies()
    ninja_values['Fossil'] = get_fossils()

    print("Welcome to Tujen Auto Buyer!")
    print("To start either input 0 to add a currency and its value or the number of coins you have")
    mode = int(input("Choose mode:")) 

    load_config()

    refresh_prices()
        
    if mode == 0:
        register()
    else:
        
        coinages = mode
        run(coinages)
    
    shutil.rmtree('./images/temp', ignore_errors=True)

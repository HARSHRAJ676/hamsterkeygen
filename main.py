import asyncio
import sys
import httpx
import random
import time
import uuid
from loguru import logger

# Disable logging for httpx
httpx_log = logger.bind(name="httpx").level("WARNING")
logger.remove()
logger.add(sink=sys.stdout, format="<white>{time:YYYY-MM-DD HH:mm:ss}</white>"
                                   " | <level>{level: <8}</level>"
                                   " | <cyan><b>{line}</b></cyan>"
                                   " - <white><b>{message}</b></white>")
logger = logger.opt(colors=True)

# Games dictionary
games = {
    1: {
        'name': 'Riding Extreme 3D',
        'appToken': 'd28721be-fd2d-4b45-869e-9f253b554e50',
        'promoId': '43e35910-c168-4634-ad4f-52fd764a843f',
        'sleep': 25000,  # in milliseconds
        'attempts': 25,
        'events_delay': 10  # in seconds
    },
    2: {
        'name': 'Chain Cube 2048',
        'appToken': 'd1690a07-3780-4068-810f-9b5bbf2931b2',
        'promoId': 'b4170868-cef0-424f-8eb9-be0622e8e8e3',
        'sleep': 25000,  # in milliseconds
        'attempts': 20,
        'events_delay': 10  # in seconds
    },
    3: {
        'name': 'My Clone Army',
        'appToken': '74ee0b5b-775e-4bee-974f-63e7f4d5bacb',
        'promoId': 'fe693b26-b342-4159-8808-15e3ff7f8767',
        'sleep': 180000,  # in milliseconds
        'attempts': 30,
        'events_delay': 10  # in seconds
    },
    4: {
        'name': 'Train Miner',
        'appToken': '82647f43-3f87-402d-88dd-09a90025313f',
        'promoId': 'c4480ac7-e178-4973-8061-9ed5b2e17954',
        'sleep': 20000,  # in milliseconds
        'attempts': 15,
        'events_delay': 10  # in seconds
    },
    5: {
        'name': 'Merge Away',
        'appToken': '8d1cc2ad-e097-4b86-90ef-7a27e19fb833',
        'promoId': 'dc128d28-c45b-411c-98ff-ac7726fbaea4',
        'sleep': 20000,  # in milliseconds
        'attempts': 25,
        'events_delay': 10  # in seconds
    },
    6: {
        'name': 'Twerk Race 3D',
        'appToken': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'promoId': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'sleep': 20000,  # in milliseconds
        'attempts': 20,
        'events_delay': 10  # in seconds
    },
    7: {
        'name': 'Polysphere',
        'appToken': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'promoId': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'sleep': 20000,  # in milliseconds
        'attempts': 20,
        'events_delay': 10  # in seconds
    },
    8: {
        'name': 'Mow and Trim',
        'appToken': 'ef319a80-949a-492e-8ee0-424fb5fc20a6',
        'promoId': 'ef319a80-949a-492e-8ee0-424fb5fc20a6',
        'sleep': 20000,  # in milliseconds
        'attempts': 20,
        'events_delay': 10  # in seconds
    },
    9: {
        'name': 'Mud Racing',
        'appToken': '8814a785-97fb-4177-9193-ca4180ff9da8',
        'promoId': '8814a785-97fb-4177-9193-ca4180ff9da8',
        'sleep': 20000,  # in milliseconds
        'attempts': 20,
        'events_delay': 10  # in seconds
    }
}

async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_numbers}"

async def make_request_with_retry(client, url, method='post', headers=None, json=None, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = await client.request(method, url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error(f"Error during request to {url}: {e}")
            retries += 1
            await asyncio.sleep(1)
    raise Exception(f"Failed after {max_retries} retries to {url}")

async def login(client_id, app_token):
    try:
        async with httpx.AsyncClient() as client:
            data = await make_request_with_retry(
                client,
                'https://api.gamepromo.io/promo/login-client',
                json={'appToken': app_token, 'clientId': client_id, 'clientOrigin': 'deviceid'}
            )
            return data['clientToken']
    except Exception as e:
        logger.error(f"Failed to login: {e}")
        raise

async def emulate_progress(client_token, promo_id):
    try:
        async with httpx.AsyncClient() as client:
            data = await make_request_with_retry(
                client,
                'https://api.gamepromo.io/promo/register-event',
                headers={'Authorization': f'Bearer {client_token}'},
                json={'promoId': promo_id, 'eventId': str(uuid.uuid4()), 'eventOrigin': 'undefined'}
            )
            return data['hasCode']
    except Exception as e:
        logger.error(f"Failed to emulate progress: {e}")
        raise

async def generate_key(client_token, promo_id):
    try:
        async with httpx.AsyncClient() as client:
            data = await make_request_with_retry(
                client,
                'https://api.gamepromo.io/promo/create-code',
                headers={'Authorization': f'Bearer {client_token}'},
                json={'promoId': promo_id}
            )
            return data['promoCode']
    except Exception as e:
        logger.error(f"Failed to generate key: {e}")
        raise

async def generate_key_process(app_token, promo_id, events_delay):
    client_id = await generate_client_id()
    try:
        client_token = await login(client_id, app_token)
    except Exception:
        return None

    for _ in range(15):  # Use game-specific attempts value or default
        await asyncio.sleep(events_delay * (random.random() / 3 + 1))
        try:
            has_code = await emulate_progress(client_token, promo_id)
        except Exception:
            continue

        if has_code:
            break

    try:
        key = await generate_key(client_token, promo_id)
        return key
    except Exception:
        return None

async def read_existing_keys(filename):
    try:
        with open(filename, 'r') as file:
            return set(line.strip() for line in file if line.strip())
    except FileNotFoundError:
        return set()

async def save_keys_to_file(filename, keys):
    try:
        with open(filename, 'w') as file:
            for key in keys:
                file.write(f"{key}\n")
    except Exception as e:
        logger.error(f"Failed to save keys to file: {e}")

async def clear_cache():
    try:
        async with httpx.AsyncClient() as client:
            await client.aclose()  # Close the client to clear its internal state and cache
        logger.info("Cache cleared successfully.")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")

async def main(game_choice, key_count):
    game = games[game_choice]
    new_keys = set()

    # Clear cache before starting
    await clear_cache()

    tasks = [generate_key_process(game['appToken'], game['promoId'], game['events_delay']) for _ in range(key_count)]
    keys = await asyncio.gather(*tasks)
    
    new_keys.update(key for key in keys if key)
    
    filename = f"{game['name'].replace(' ', '_').lower()}_keys.txt"
    existing_keys = await read_existing_keys(filename)
    
    all_keys = existing_keys.union(new_keys)
    
    await save_keys_to_file(filename, all_keys)
    
    return list(new_keys), game['name']

if __name__ == "__main__":
    print("Select a game:")
    for key, value in games.items():
        print(f"{key}: {value['name']}")
    game_choice = int(input("Enter the game number: "))
    key_count = int(input("Enter the number of keys to generate: "))

    logger.info(f"Generating {key_count} key(s) for {games[game_choice]['name']} using system network")
    keys, game_name = asyncio.run(main(game_choice, key_count))
    if keys:
        logger.success(f"Generated Key(s) for {game_name}:")
        for key in keys:
            logger.success(key)
    else:
        logger.error("No keys were generated.")

    input("Press enter to exit")

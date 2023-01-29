#!/home/stastodd/projects/internet_accessibility_checking/venv/bin/python3.8

import yaml
import asyncio
from icmplib import async_multiping
import os
import time
from datetime import datetime
import aiohttp


async def send_textmessage_to_tbot(url, one_data):
    """
    Courutine with aiohttp lib for send request with text

    :param url: https://api.telegram.org/bot{tbot_api_token}/sendMessage
    :param one_data: {"chat_id": "01010101010", "text": 'sometext'}
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=one_data) as response:
            return await response.text()


def downtime_message_creator(stop_inet_file_data, current_datetime):
    """
    Create message that will be sent to telegram. Example:
        Internet downtime is DOWNTIME\n Inet is down from x to x

    :param stop_inet_file_data: '1675009767'
    :param current_datetime: 1675009867
    :return:
    """
    downtime_from = datetime.fromtimestamp(int(stop_inet_file_data))
    downtime_to = datetime.fromtimestamp(int(current_datetime))
    return f"Currently, the Internet is running!\n" \
           f"Previously it work was down:\n" \
           f"from: {downtime_from.strftime('%Y-%m-%d, %H:%M:%S')}\n" \
           f"to:     {downtime_to.strftime('%Y-%m-%d, %H:%M:%S')}"


def get_data_from_yaml(filename):
    """
    Get data from yaml
    :param filename: 'filename.yaml'
    :return: {key: values}
    """
    with open(filename, "r") as f:
        return yaml.safe_load(f)


async def are_alive(*addresses, **kwargs):
    """
    async ping
    :param addresses: ['1.1.1.1', '8.8.8.8']
    :param kwargs:
        {"count": 2,
         "privileged": False,
         "timeout": 5}
    :return: [True, False]
    """
    result = list()
    hosts = await async_multiping(*addresses, **kwargs)
    for host in hosts:
        if not host.is_alive:
            result.append(False)
        else:
            result.append(True)
    return result


async def main(config_data):
    # Get all config params:
    api_telegram_token = config_data.get("api_telegram_token")
    admins_ids = config_data.get("admins_ids", list())
    inet_access_check_data = config_data.get("internet_accessibility_checking_params", dict())

    # Url for send requests with textmessage:
    url_textmessage = f"https://api.telegram.org/bot{api_telegram_token}/sendMessage"

    # Config params:
    enable_status = inet_access_check_data.get("enable_status", True)
    telegram_bot_notification = inet_access_check_data.get("telegram_bot_notification", True)
    check_address1 = inet_access_check_data.get("check_address1", "8.8.8.8")
    check_address2 = inet_access_check_data.get("check_address2", "1.1.1.1")
    number_of_requests = inet_access_check_data.get("number_of_requests", 2)
    pause_seconds_between_attempts = inet_access_check_data.get("pause_seconds_between_attempts", 60)
    stop_inet_filename = inet_access_check_data.get("stop_inet_filename", "stop_inet_datetime.txt")

    if not enable_status:
        return

    # Ping procedure:
    kwargs = {"count": number_of_requests,
              "privileged": False,
              "timeout": 3}

    while enable_status:
        ping_result = await are_alive([check_address1, check_address2], **kwargs)  # [True, False]

        # Check that start_inet_filename and stop_inet_filename files are exist. If no, create:
        if not os.path.isfile(stop_inet_filename):
            with open(stop_inet_filename, "w") as file:
                file.write("\n")

        # Update datetime in the output_filename file:
        current_datetime = int(time.time())  # epoch format: 1674991904
        if any(ping_result):  # if we have at least one True
            # Detect exist row inside file:
            with open(stop_inet_filename, "r") as file:
                stop_inet_file_data = file.read().strip()
            # if stop_inet_file_data:
            if stop_inet_file_data:
                # Send message to admins of telegram bot:
                if telegram_bot_notification:
                    send_message = downtime_message_creator(stop_inet_file_data, current_datetime)
                    all_data_to_send = [{"chat_id": list(adm.values())[0], 'text': send_message} for adm in admins_ids]
                    coroutines = [send_textmessage_to_tbot(url_textmessage, one_data) for one_data in all_data_to_send]
                    await asyncio.gather(*coroutines)
                    # Delete datetime in stop_inet_filename:
                    with open(stop_inet_filename, "w") as file:
                        file.write("\n")
        else:
            # Detect exist row inside file:
            with open(stop_inet_filename, "r") as file:
                stop_inet_file_data = file.read().strip()
            # If file is empty, write new datetime:
            if not stop_inet_file_data:
                with open(stop_inet_filename, "w") as file:
                    file.write(str(current_datetime))

        await asyncio.sleep(pause_seconds_between_attempts)


if __name__ == "__main__":
    config_data = get_data_from_yaml("data.yaml")
    asyncio.run(main(config_data))

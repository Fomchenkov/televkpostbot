#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import eventlet
import requests
import logging
import telebot
import config


SERVICE_TOKEN = "7320876373208763732087631d7379135977320732087632a62d78c736ea392a738de82"
GROUP_ID = 101398842
URL_VK = 'https://api.vk.com/method/wall.get?owner_id=-' + str(GROUP_ID) + '&count=20&filter=owner&access_token=' + SERVICE_TOKEN
BASE_POST_URL = 'https://vk.com/wall-' + str(GROUP_ID) + '_'
FILENAME_VK = 'last_known_id.txt'
BOT_TOKEN = config.BOT_TOKEN
CHANNEL_NAME = config.CHANNEL_NAME

bot = telebot.TeleBot(BOT_TOKEN)


def get_data():
	"""
	Get new VK wall posts
	"""
	timeout = eventlet.Timeout(10)
	try:
		feed = requests.get(URL_VK)
		return feed.json()
	except eventlet.timeout.Timeout:
		logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
		return None
	finally:
		timeout.cancel()


def send_new_posts(items, last_id):
	"""
	Send new posts into channel
	"""
	for item in items:
		if item['id'] <= last_id:
			break
		link = '{!s}{!s}'.format(BASE_POST_URL, item['id'])
		bot.send_message(CHANNEL_NAME, link)
		time.sleep(1)
	return  


def check_new_posts_vk():
	"""
	Check new post vk wall
	"""
	logging.info('[VK] Started scanning for new posts')
	with open(FILENAME_VK, 'rt') as file:
		last_id = int(file.read())
		if last_id is None:
			logging.error('Could not read from storage. Skipped iteration.')
			return
		logging.info('Previous last_id is {!s}'.format(last_id))
	try:
		feed = get_data()
		if feed is not None:
			entries = feed['response'][1:]
			try:
				tmp = entries[0]['is_pinned']
				send_new_posts(entries[1:], last_id)
			except KeyError:
				send_new_posts(entries, last_id)
			with open(FILENAME_VK, 'wt') as file:
				try:
					tmp = entries[0]['is_pinned']
					file.write(str(entries[1]['id']))
					logging.info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
				except KeyError:
					file.write(str(entries[0]['id']))
					logging.info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
	except Exception as ex:
		logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
		pass
	logging.info('[VK] Finished scanning')
	return


if __name__ == '__main__':
	logging.getLogger('requests').setLevel(logging.CRITICAL)
	logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', 
						level=logging.INFO, filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
	while True:
		check_new_posts_vk()
		logging.info('[App] Script went to sleep.')
		try:
			time.sleep(1 * 4)
		except KeyboardInterrupt: 
			exit()
	logging.info('[App] Script exited.\n')

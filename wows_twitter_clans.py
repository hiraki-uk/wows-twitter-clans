import asyncio
import datetime
import json
import math
import os
import random

import twitter
from dotenv import load_dotenv
from twitter.twitter_utils import \
    calc_expected_status_length as calc_status_length
from wowspy import Wows

from logger import Logger


load_dotenv(dotenv_path='.env')


class Twitterclans:
	def __init__(self, key, secret_key, token, token_secret, api_key):
		self.twitter_api = twitter.Api(
			consumer_key = key,
			consumer_secret = secret_key,
			access_token_key = token,
			access_token_secret = token_secret
		)
		self.wows_api = Wows(api_key)
		self.logger = Logger(__name__)


	async def start(self):
		"""
		Super super driver a super driver!
		"""
		self.logger.info('Starting twitter-clan-tweeter.')
		while 1:
			try:
				total = self._get_clan_total()
				# get status
				while 1:
					clan_index = random.randint(1, total)
					clan_id = self._get_clan_id(clan_index)
					clan_detail = self._get_clan_detail(clan_id)
					status = _create_status(clan_detail)
					if status is not None:
						break

				# tweet
				final_status = _optimize_status(status)
				self.logger.debug(f'tweeting:\n{final_status}')
				self.twitter_api.PostUpdate(final_status)
				self.logger.debug(f'Tweeted.')

			except Exception as e:
				self.logger.critical(e)
			await asyncio.sleep(60*60)
	

	def _get_clan_total(self) -> int:
		clans = self.wows_api.clans(self.wows_api.region.AS, language='ja', limit=1)
		return clans['meta']['total'] 

	def _get_clan_id(self, clan_index: int):
		clan = self.wows_api.clans(self.wows_api.region.AS, language='ja', limit=1, page_no=clan_index)
		return clan['data'][0]['clan_id']


	def _get_clan_detail(self, clan_id: int):
		detail = self.wows_api.clan_details(self.wows_api.region.AS, language='ja', clan_id=clan_id)
		return detail['data'][str(clan_id)]


def _create_status(detail):
	if detail['members_count'] < 6:
		return None
	elif detail['is_clan_disbanded'] is True:
		return None

	tag = detail['tag']
	members_count = detail['members_count']
	name = detail['name']
	creator_name = detail['creator_name']
	created_at = detail['created_at']
	leader_name = detail['leader_name']
	description = detail['description']

	status = f'[{tag}] {name}\n' \
			f'クラマス：{leader_name}　在籍数：{members_count}\n\n' \
			f'{description}'
	return status


def _optimize_status(status):
	# if over 280 limit shorten status
	status.replace('@', '@/')
	status.replace('＠', '@/')
	temp_status = status
	if not calc_status_length(temp_status) < 270:
		# using while as removing exceed_length not always work 
		# due to 2 length letters and 1 length letters
		while 270 < calc_status_length(temp_status):
			exceed_length = (270 - calc_status_length(temp_status)) // 2
			status = status[:exceed_length]
			temp_status = f'{status}...'
	final_status = temp_status
	return final_status


if __name__ == '__main__':
	key = os.getenv('KEY')
	secret_key = os.getenv('KEY_SECRET')
	token = os.getenv('TOKEN')
	secret_token = os.getenv('TOKEN_SECRET')
	api_key = os.getenv('API_KEY')

	tc = Twitterclans(
		key,
		secret_key,
		token,
		secret_token,
		api_key
	)

	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(
			asyncio.wait([
				tc.start()
			])
		)
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()

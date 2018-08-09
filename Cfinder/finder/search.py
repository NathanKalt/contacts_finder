import requests
from .duckduckgo import get_zci
import html2text
from bs4 import BeautifulSoup as bs
from collections import defaultdict
import re
import phonenumbers
from flanker.addresslib import address
from pprint import pprint 
from urllib.parse import urljoin
from fake_useragent import UserAgent
import jmespath

class FindPerson(object):

	def __init__(self):
		self.query = {} 
		self.info = {}
		self.ua =  UserAgent()
		self.url = ''

	### BROWSING METHODS
	def headless_page_content(self, url):
		text = requests.get('http://localhost:8050/render.html', params={'url': url, 'wait': 2}).content.decode('utf8')
		return text


	def page_content(self, url):
		response = requests.get('http://localhost:8050/render.html', params={'url': url, 'wait': 2})
		return response.text
	###################

	def get_data(self, query):
		self.url = get_zci(query['name'] + ' ' +query['keyword']+ ' ' +query['location'])
		info, links = self.process_url(self.url, {})
	
		if len(info['emails']) == 0:
			info = self.extend_contacts(links, info)
		return info
		self.driver.close()

	def process_url(self, url, info):
		if 'facebook' in url: text = self.headless_page_content(url)
		else: text = self.page_content(url)

		soup = bs(text, "lxml")	
		links = []
		for link in soup.findAll('a'):
			if link not in ["", None]:
				links.append(link.get('href', ""))
		info['base_url'] = url
		info['phones'] = self.get_phones(text, [])
		info['emails'] = self.get_emails(text, [])
		info = self.get_socials(links, info, url)

		return info, links

	def extend_contacts(self, links, info):
		choise = ['contact', 'about']
		contactsurl =  list(set([l for l in links if any(x in l for x in choise)])) 
		for u in contactsurl: 
			u = urljoin(self.url, u)
			if 'facebook' in u: text =  self.headless_page_content(u)
			else: text = self.page_content(u)
			soup = bs(text, "lxml")
			links = []
			for link in soup.findAll('a'):
				if link not in ["", None]:
					links.append(link.get('href', ""))
			info['emails'] = self.get_emails(text, info['emails'])
			info['phones'] = self.get_phones(text, info['phones'])
			info = self.get_socials(links, info, u)
		return info

	
	def get_phones(self, text, phones):
		for match in phonenumbers.PhoneNumberMatcher(text, 'US'):
			phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164))
		phones = list(set(phones))
		return phones

	def get_emails(self, text, emails):
		email = re.findall(r"[\w\.-]+@[\w\.-]+[.]+[a-zA-Z]{2,5}", text)
		email = [e for e in email if e not in ['', None] + emails]
		email = [e for e in email if address.parse(e) != None]
		email = [e for e in email if e not in ['', None] + emails]
		email = [e.lower() for e in list(set(email))]
		email = email+emails
		return list(set(email))

	def get_socials(self, links, info, url):
		socials = [('facebook', 'facebook'), 
					('linkedin', 'linkedin'), 
					('vk', 'vk.com'), 
					('telegram', 't.me'), 
					('instagram', 'instagram')]

		if 'facebook' in url:
			socials = socials[1:]
		for item in socials:
			if jmespath.search(item[0], info) is not None: add = info[item[0]] 
			else: add = []
			results = list( set([l for l in links if item[1] in l] + add )) 
			info[item[0]] = results	
		return info

	def validate(self, email):
		if validate_email(email): return email
	
	
	def process_facebook(self, url):
		text = self.headless_page_content(url)
		soup = bs(text, "lxml")	
		if '/schema.org/' in text:
			self.process_company_facebook(text, soup)
		else:
			self.process_person_facebook(text, soup)

	
	def process_company_facebook(self, text, soup):
		links = []
		for link in soup.findAll('a'):
			if link not in ["", None]:
				links.append(link.get('href', ""))
		# info['base_url'] = url
		info['phones'] = self.get_phones(text, [])
		info['emails'] = self.get_emails(text, [])
		info = self.get_socials(links, info, url)
		#find person facebook page

		#get address

	


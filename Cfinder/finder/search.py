from flanker.addresslib import address
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
from .query import get_zci
from pprint import pprint 
import phonenumbers
import html2text
import jmespath
import requests
import re

#WARN run splash on port 8050
# eval $(docker-machine env default)
# docker run -p 8050:8050 scrapinghub/splash -v3

class FindPerson(object):
	''' CLASS TO FIND PERSON INFO & contact data'''
	def __init__(self):
		self.query = {} 
		self.info = {}
		self.info['socials'] = {}
		self.info['emails'] = []
		self.info['phones'] = []
		self.ua = UserAgent()
		self.url = ''
		self.to_see = ['website', 'facebook', 'linkedin']
		

	def get_data(self, query):
		''' the process starts here '''
		url = get_zci(self.query['name'] + ' ' +self.query['keyword']+ ' ' +self.query['location'])
		# print (url)
		self.start(url)
		pprint (self.info)
		return self.info

	def start(self, url):
		''' simple requests sequence scheduler '''
		if 'facebook' in url:
			self.info['socials']['facebook'] = [url]
			self.to_see.remove('facebook')
			self.process_facebook(url)
		elif 'linkedin' in url: 
			self.info['socials']['linkedin'] = [url]
			self.to_see.remove('linkedin')
		else:
			self.info['website'] = [url]
			self.to_see.remove('website')
			self.process_company_page(url)
		
		for e in self.to_see:
			if e == 'facebook':
				fblinks = jmespath.search('socials.facebook', self.info) 
				[self.process_facebook(f) for f in fblinks ]
			if e == 'website':
				self.process_company_page(url)

	### BROWSING METHODS #####################################
	def headless_page_content(self, url):
		'''WARN: ENABLE SPLASH ON PORT 8050 FOR HEADLESS BROWSING'''
		headers={'User-Agent': self.ua.random}
		text = requests.get('http://192.168.99.100:8050/render.html', params={'url': url, 'wait': 2}, headers=headers).content.decode('utf8')
		soup = bs(text, "lxml")	
		return text, soup

	def page_content(self, url):
		response = requests.get(url, headers={'User-Agent': self.ua.random})
		text = response.content.decode('utf8')
		soup = bs(text, 'lxml')
		return text, soup

	###### DATA RETRIEWING METHODS ###########################
	def get_phones(self, text):
		''' extracts phones from webpage '''
		phones = []
		for match in phonenumbers.PhoneNumberMatcher(text, ''):
			phones.append(phonenumbers.format_number(match.number, ))
		phones = list(set(phones+self.info['phones']))
		return phones

	def get_emails(self, text):
		''' extracts emails from webpage '''
		email = re.findall(r"[\w\.-]+@[\w\.-]+[.]+[a-zA-Z]{2,5}", text)
		email = [e for e in email if e not in ['', None]]
		email = [e for e in email if address.parse(e) != None]
		email = [e for e in email if e not in ['', None]]
		email = [e.lower() for e in list(set(email))]
		return list(set(email+self.info['emails']))

	def fetch_links(self, soup):
		''' fetches all links from an webpage '''
		links = [l.get('href', "") for l in soup.findAll('a') if l not in ["", None] ]
		return links

	def get_socials(self, soup, url, socials):
		''' fetches all social links from an webpage '''
		if not socials: socials = {}
		links = self.fetch_links(soup)
		socialtypes = [('facebook', 'facebook'), ('linkedin', 'linkedin'), ('vk', 'vk.com'), ('telegram', 't.me'), ('instagram', 'instagram'), ('twitter', 'twitter')]

		if 'facebook' in url:
			socialtypes = socialtypes[1:]

		for item in socialtypes:
			if jmespath.search(item[0], socials) is not None: add = socials[item[0]] 
			else: add = []
			results = list( set([l for l in links if item[1] in l] + add )) 
			socials[item[0]] = results	
		return socials

	def search_near_tag(self, soup, query):
		'''in development '''
		r = r"^ *"+query+"*$"
		for elem in soup(text=re.compile(r, re.IGNORECASE)):
			for i in range(0,1):
				elem = elem.findNext('p')

	###### PAGE TYPES DBROWSING METHODS ###########################
	#company webpage methods
	def process_company_page(self, url):

		# print ('processing company page')
		text, soup = self.headless_page_content(url)
		self.info['url'] = url
		self.info['emails'] = self.get_emails(text)
		self.info['phones'] = self.get_phones(text)
		self.info['socials'] = self.get_socials(soup, url, jmespath.search('socials', self.info))
		if len(self.info['emails']) == 0:
			# print ('improving contacts')
			links = self.fetch_links(soup)
			self.extend_contacts(links, url)

	def extend_contacts(self, links, url):
		''' find proper contact pages '''
		choise = ['contact', 'about', 'team']
		contactsurl =  list(set([l for l in links if any(x in l for x in choise)])) 
		for u in contactsurl: 
			u = urljoin(url, u)
			print (u)
			text, soup = self.headless_page_content(u)
			self.info['emails']  =  self.get_emails(text)
			self.info['phones']  =  self.get_phones(text)
			self.info['socials'] =  self.get_socials(soup, url, jmespath.search('socials', self.info))
			self.search_near_tag(soup, self.query['name'])

	#facebook methods
	def process_facebook(self, url):
		text, soup = self.headless_page_content(url)
		if '/schema.org/' in text:
			print ('company facebook page')
			self.info['facebook_company_url'] = url
			self.process_cfp(text, soup, url)
		else:
			# change logic to personal page
			print ('personal facebook page')
			self.info['facebook_personal_url'] = url
			self.process_cfp(text, soup, url)


	def process_cfp(self, text, soup, url):
		'''browse company facebook page '''
		self.info['facebook_company_emails'] = self.get_emails(text)
		self.info['facebook_company_phones'] = self.get_phones(text)
		self.info['socials'] = self.get_socials(soup, url, jmespath.search('socials', self.info))
		self.search_near_tag(soup, self.query['name'])
		links = self.fetch_links(soup)
		# not working properly -> use search near tag or modyfy the method
		personal_page = list( set([l for l in links if self.query['name'] in l.lower()])) 
		print ('personal page is ', personal_page)

	
	def process_pfp(self, text, soup, url):
		''' browse personal facebook page '''
		self.info['facebook_personal_emails'] = self.get_emails(text)
		self.info['facebook_personal_phones'] = self.get_phones(text)
		self.info['socials'] = self.get_socials(soup, url, jmespath.search('socials', self.info))
		self.search_near_tag(soup, self.query['name'])
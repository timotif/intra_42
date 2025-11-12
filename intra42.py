import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

class IntraScrape:
	SELECTORS = {
		'projects_list': 'ul.projects-list--list',
		'project_item': 'li.project-item',
		'project_name': 'div.project-name',
		'attachment_name': 'h4.attachment-name'
	}
	
	def __init__(self, cookies):
		self.session = requests.Session()
		self.session.cookies.update(cookies)
		self.all_projects = []
		self.base_url = "https://projects.intra.42.fr"
	
	def _get_project_list(self):
		"""
		Helper method to retrieve the raw list of project items from the projects page.
		Returns:
			list[BeautifulSoup Tag]: List of project item HTML elements
		"""
		url = self.base_url + "/projects/list"
		response = self.session.get(url)
		if response.status_code != 200:
			raise Exception(f"Failed to retrieve projects: {response.status_code}")
		soup = BeautifulSoup(response.text, 'html.parser')
		# Use select_one() to find the first matching element
		projects_ul = soup.select_one(self.SELECTORS['projects_list'])
		if not projects_ul:
			raise Exception("Projects list not found in the page")
		# Use select() to find all matching elements
		project_items = projects_ul.select(self.SELECTORS['project_item'])
		return project_items

	def get_projects(self) -> list[dict]:
		"""
		Retrieves the list of projects from the 42 intra projects page.
		Returns:
			list[dict]: List of projects with 'name' and 'url' keys
		"""
		all_projects = []
		project_items = self._get_project_list()
		for item in project_items:
			# Use select_one() with the selector from SELECTORS
			project_name_div = item.select_one(self.SELECTORS['project_name'])
			if not project_name_div:
				continue
			project_link = project_name_div.find('a')
			if not project_link:
				continue
			all_projects.append({
				'name': project_link.text.strip(),
				'url': project_link['href']
			})
		self.all_projects = all_projects
		return all_projects
	
	def get_project_attachments(self, project_url: str) -> list[str]:
		"""
		Retrieves the list of attachment links for a given project.
		Args:
			project_url (str): URL path of the project
		Returns:
			list[str]: List of attachment URLs
		"""
		url = self.base_url + project_url
		response = self.session.get(url)
		if response.status_code != 200:
			raise Exception(f"Failed to retrieve project page: {response.status_code}")
		soup = BeautifulSoup(response.text, 'html.parser')
		# Use select() to find all matching elements
		attachments_div = soup.select(self.SELECTORS['attachment_name'])
		if not attachments_div:
			print("No attachments found for this project.")
			return []
		links = [att.find('a')['href'] for att in attachments_div if att.find('a')]
		return links
	
	def get_project_url_by_name(self, project_name: str) -> str:
		"""
		Retrieves the URL of a project given its name.
		Args:
			project_name (str): Name of the project to search for
		Returns:
			str: URL of the project or None if not found
		"""
		if not self.all_projects:
			self.get_projects()
		url = [proj['url'] for proj in self.all_projects if proj['name'].lower() == project_name.lower()]
		return url[0] if url else None

	def download_attachment(self, attachment_url: str, save_path: str, show_progress: bool = True):
		"""
		Download an attachment with optional progress bar

		Args:
			attachment_url (str): URL of the attachment to download
			save_path (str): Path where to save the file
			show_progress (bool): Whether to show a progress bar for large files (default: True)
		"""
		with self.session.get(attachment_url, stream=True, timeout=30) as response:
			if response.status_code != 200:
				raise Exception(f"Failed to download attachment: {response.status_code}")

			# Get total file size from headers
			total_size = int(response.headers.get('content-length', 0))

			# Only show progress bar for files larger than 1MB
			if show_progress and total_size > 1_000_000:
				# Extract filename for progress bar description
				filename = save_path.split('/')[-1]
				progress_bar = tqdm(
					total=total_size,
					unit='B',
					unit_scale=True,
					unit_divisor=1024,
					desc=f"    {filename}",
					leave=False
				)
			else:
				progress_bar = None

			with open(save_path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=8192):
					if chunk:
						f.write(chunk)
						if progress_bar:
							progress_bar.update(len(chunk))

			if progress_bar:
				progress_bar.close()

class IntraAPI:
	def __init__(self, uid, secret):
		self.uid = uid
		self.secret = secret
		self.url = "https://api.intra.42.fr"
		self.headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		}
		self.token = None
		self.get_token()
	
	def get(self, endpoint, params=None, page=None, page_size=30):
		"""
		Get request to the 42 API with optional pagination

		Args:
			endpoint (str): API endpoint
			params (dict, optional): Query parameters. Defaults to {}.
			page (int, optional): Page number for pagination. Defaults to None.
			page_size (int, optional): Number of items per page. Defaults to 30.
		"""
		if params is None:
			params = {}
		params = params.copy()
		if page is not None:
			params['page[number]'] = page
			params['page[size]'] = page_size
		if self.token:
			self.headers['Authorization'] = 'Bearer ' + self.token
		response = requests.get(
			self.url + endpoint, 
			headers=self.headers, 
			params=params
		)
		response.raise_for_status()
		try:
			return response.json()
		except requests.JSONDecodeError:
			raise Exception(f"Invalid JSON response from {endpoint}")

	def get_paginated(self, endpoint, params=None, page_size=100):
		"""
		Generator to get all items from a paginated endpoint

		Args:
			endpoint (str): API endpoint
			params (dict, optional): Query parameters. Defaults to {}.
			page_size (int, optional): Number of items per page. Defaults to 100.
		Yields:
			dict: Individual items from the paginated response
		"""
		if params is None:
			params = {}
		params = params.copy()
		page = 1
		while True:
			params['page[number]'] = page
			params['page[size]'] = page_size
			results = self.get(endpoint, params=params)
			if not results:
				break
			for item in results:
				yield item
			if len(results) < page_size:
				break
			page += 1
	
	def get_all_pages(self, endpoint, params={}, page_size=100):
		return list(self.get_paginated(endpoint, params=params, page_size=page_size))

	def post(self, endpoint, payload={}):
		if self.token:
			self.headers['Authorization'] = 'Bearer ' + self.token
		response = requests.post(
			self.url + endpoint, 
			headers=self.headers, 
			data=payload
		)
		return response.json()

	def get_token(self):
		oauth_response = self.post("/oauth/token", {"grant_type": "client_credentials", \
                            "client_id": self.uid, "client_secret": self.secret})
		if not oauth_response.get("access_token"):
			raise Exception(oauth_response.get("error_description"))
		self.token = oauth_response["access_token"]

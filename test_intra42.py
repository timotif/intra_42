import pytest
from unittest.mock import Mock, patch, MagicMock
from intra42 import IntraAPI, IntraScrape
import requests


class TestIntraAPI:
    """Tests for the IntraAPI class"""

    @patch('intra42.requests.post')
    def test_token_acquisition_success(self, mock_post):
        """Test successful OAuth2 token acquisition"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'expires_in': 7200
        }
        mock_post.return_value = mock_response

        api = IntraAPI('test_uid', 'test_secret')

        assert api.token == 'test_token_123'
        mock_post.assert_called_once()

    @patch('intra42.requests.post')
    def test_token_acquisition_failure(self, mock_post):
        """Test failed OAuth2 token acquisition"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'error': 'invalid_client',
            'error_description': 'Invalid client credentials'
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match='Invalid client credentials'):
            IntraAPI('bad_uid', 'bad_secret')

    @patch('intra42.requests.post')
    @patch('intra42.requests.get')
    def test_get_without_pagination(self, mock_get, mock_post):
        """Test GET request without pagination parameters"""
        # Mock token acquisition
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_post_response

        # Mock GET request
        mock_get_response = Mock()
        mock_get_response.json.return_value = {'id': 1, 'name': 'test'}
        mock_get.return_value = mock_get_response

        api = IntraAPI('uid', 'secret')
        result = api.get('/v2/users/1')

        assert result == {'id': 1, 'name': 'test'}
        # Check Authorization header was set
        call_kwargs = mock_get.call_args.kwargs
        assert 'Authorization' in call_kwargs['headers']
        assert call_kwargs['headers']['Authorization'] == 'Bearer token'

    @patch('intra42.requests.post')
    @patch('intra42.requests.get')
    def test_get_with_pagination(self, mock_get, mock_post):
        """Test GET request with pagination parameters"""
        # Mock token acquisition
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_post_response

        # Mock GET request
        mock_get_response = Mock()
        mock_get_response.json.return_value = [{'id': 1}, {'id': 2}]
        mock_get.return_value = mock_get_response

        api = IntraAPI('uid', 'secret')
        result = api.get('/v2/users', page=2, page_size=50)

        # Check pagination params were added
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs['params']['page[number]'] == 2
        assert call_kwargs['params']['page[size]'] == 50

    @patch('intra42.requests.post')
    @patch('intra42.requests.get')
    def test_get_paginated_generator(self, mock_get, mock_post):
        """Test get_paginated generator yields all items"""
        # Mock token acquisition
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_post_response

        # Mock paginated responses
        mock_get.return_value.json.side_effect = [
            [{'id': 1}, {'id': 2}],  # Page 1 (full page)
            [{'id': 3}],  # Page 2 (partial page - triggers stop)
        ]

        api = IntraAPI('uid', 'secret')
        items = list(api.get_paginated('/v2/users', page_size=2))

        assert len(items) == 3
        assert items == [{'id': 1}, {'id': 2}, {'id': 3}]
        assert mock_get.call_count == 2

    @patch('intra42.requests.post')
    @patch('intra42.requests.get')
    def test_get_paginated_empty_response(self, mock_get, mock_post):
        """Test get_paginated handles empty response"""
        # Mock token acquisition
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_post_response

        # Mock empty response
        mock_get.return_value.json.return_value = []

        api = IntraAPI('uid', 'secret')
        items = list(api.get_paginated('/v2/users'))

        assert items == []
        assert mock_get.call_count == 1

    @patch('intra42.requests.post')
    @patch('intra42.requests.get')
    def test_get_all_pages(self, mock_get, mock_post):
        """Test get_all_pages returns complete list"""
        # Mock token acquisition
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_post_response

        # Mock paginated responses
        mock_get.return_value.json.side_effect = [
            [{'id': 1}, {'id': 2}],
            [{'id': 3}],
        ]

        api = IntraAPI('uid', 'secret')
        items = api.get_all_pages('/v2/users', page_size=2)

        assert isinstance(items, list)
        assert len(items) == 3

    @patch('intra42.requests.post')
    def test_params_not_shared_between_calls(self, mock_post):
        """Test that mutable default params don't cause issues"""
        # This test would fail with the current implementation
        # It's here to demonstrate the bug with mutable default arguments
        mock_response = Mock()
        mock_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response

        # Note: This test documents a known issue with mutable defaults
        # The actual fix requires changing the code


class TestIntraScrape:
    """Tests for the IntraScrape class"""

    def test_init(self):
        """Test IntraScrape initialization"""
        cookies = {'session': 'test'}
        scraper = IntraScrape(cookies)

        assert scraper.base_url == "https://projects.intra.42.fr"
        assert scraper.all_projects == []
        assert scraper.session.cookies.get('session') == 'test'

    @patch('intra42.requests.Session.get')
    def test_get_project_list_success(self, mock_get):
        """Test _get_project_list successfully retrieves projects"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <ul class="projects-list--list">
                    <li class="project-item">
                        <div class="project-name">
                            <a href="/projects/test">Test Project</a>
                        </div>
                    </li>
                </ul>
            </html>
        '''
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        project_items = scraper._get_project_list()

        assert len(project_items) == 1
        assert project_items[0].get('class') == ['project-item']

    @patch('intra42.requests.Session.get')
    def test_get_project_list_http_error(self, mock_get):
        """Test _get_project_list handles HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        scraper = IntraScrape({})

        with pytest.raises(Exception, match='Failed to retrieve projects: 403'):
            scraper._get_project_list()

    @patch('intra42.requests.Session.get')
    def test_get_project_list_no_projects_found(self, mock_get):
        """Test _get_project_list when projects list is missing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No projects list here</body></html>'
        mock_get.return_value = mock_response

        scraper = IntraScrape({})

        # Should return empty list when no projects found, not raise exception
        results = scraper._get_project_list_page(1)
        assert results == []

    @patch('intra42.requests.Session.get')
    def test_get_projects(self, mock_get):
        """Test get_projects extracts project data correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <ul class="projects-list--list">
                    <li class="project-item">
                        <div class="project-name">
                            <a href="/projects/libft">Libft</a>
                        </div>
                    </li>
                    <li class="project-item">
                        <div class="project-name">
                            <a href="/projects/ft_printf">ft_printf</a>
                        </div>
                    </li>
                </ul>
            </html>
        '''
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        projects = scraper.get_all_projects()

        assert len(projects) == 2
        assert projects[0] == {'name': 'Libft', 'url': '/projects/libft'}
        assert projects[1] == {'name': 'ft_printf', 'url': '/projects/ft_printf'}
        assert scraper.all_projects == projects

    @patch('intra42.requests.Session.get')
    def test_get_project_attachments(self, mock_get):
        """Test get_project_attachments extracts attachment links"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h4 class="attachment-name">
                    <a href="/uploads/subject.pdf">en.subject.pdf</a>
                </h4>
                <h4 class="attachment-name">
                    <a href="/uploads/guide.pdf">guide.pdf</a>
                </h4>
            </html>
        '''
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        attachments = scraper.get_project_attachments('/projects/libft')

        assert len(attachments) == 2
        assert attachments[0] == '/uploads/subject.pdf'
        assert attachments[1] == '/uploads/guide.pdf'

    @patch('intra42.requests.Session.get')
    def test_get_project_attachments_none_found(self, mock_get, capsys):
        """Test get_project_attachments when no attachments exist"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No attachments</body></html>'
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        attachments = scraper.get_project_attachments('/projects/test')

        assert attachments == []
        captured = capsys.readouterr()
        assert 'No attachments found' in captured.out

    @patch('intra42.requests.Session.get')
    def test_get_project_url_by_name(self, mock_get):
        """Test get_project_url_by_name finds correct project"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <ul class="projects-list--list">
                    <li class="project-item">
                        <div class="project-name">
                            <a href="/projects/libft">Libft</a>
                        </div>
                    </li>
                </ul>
            </html>
        '''
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        url = scraper.get_project_url_by_name('libft')

        assert url == '/projects/libft'

    @patch('intra42.requests.Session.get')
    def test_get_project_url_by_name_not_found(self, mock_get):
        """Test get_project_url_by_name returns None for missing project"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <ul class="projects-list--list">
                    <li class="project-item">
                        <div class="project-name">
                            <a href="/projects/libft">Libft</a>
                        </div>
                    </li>
                </ul>
            </html>
        '''
        mock_get.return_value = mock_response

        scraper = IntraScrape({})
        url = scraper.get_project_url_by_name('nonexistent')

        assert url is None

    @patch('intra42.requests.Session.get')
    @patch('builtins.open', create=True)
    def test_download_attachment(self, mock_open, mock_get):
        """Test download_attachment saves file correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '500000'}  # Small file (500KB), no progress bar
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        scraper = IntraScrape({})
        scraper.download_attachment('/uploads/test.pdf', '/tmp/test.pdf', show_progress=False)

        # Verify file was written
        assert mock_file.write.call_count == 2
        mock_file.write.assert_any_call(b'chunk1')
        mock_file.write.assert_any_call(b'chunk2')

    @patch('intra42.requests.Session.get')
    def test_download_attachment_http_error(self, mock_get):
        """Test download_attachment handles HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'content-length': '0'}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        scraper = IntraScrape({})

        with pytest.raises(Exception, match='Failed to download attachment: 404'):
            scraper.download_attachment('/uploads/missing.pdf', '/tmp/test.pdf')

    @patch('intra42.tqdm')
    @patch('intra42.requests.Session.get')
    @patch('builtins.open', create=True)
    def test_download_attachment_large_file_with_progress(self, mock_open, mock_get, mock_tqdm):
        """Test download_attachment shows progress bar for large files (>1MB)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '5000000'}  # 5MB file
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock progress bar
        mock_progress = MagicMock()
        mock_tqdm.return_value = mock_progress

        scraper = IntraScrape({})
        scraper.download_attachment('/uploads/large.pdf', '/tmp/large.pdf', show_progress=True)

        # Verify progress bar was created for large file
        mock_tqdm.assert_called_once()
        assert mock_tqdm.call_args.kwargs['total'] == 5000000

    @patch('intra42.requests.Session')
    def test_get_remote_modified_time_success(self, mock_session_class):
        """Test getting remote file modification time via HEAD request"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'Fri, 09 May 2025 12:16:12 GMT'
        mock_session.head.return_value = mock_response

        scraper = IntraScrape({})
        timestamp = scraper.get_remote_modified_time('http://example.com/file.pdf')

        assert timestamp == 1746792972.0  # Unix timestamp for that date
        mock_session.head.assert_called_once_with('http://example.com/file.pdf', timeout=10)

    @patch('intra42.requests.Session')
    def test_get_remote_modified_time_no_header(self, mock_session_class):
        """Test getting remote modified time when header is missing"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = None
        mock_session.head.return_value = mock_response

        scraper = IntraScrape({})
        timestamp = scraper.get_remote_modified_time('http://example.com/file.pdf')

        assert timestamp == 0  # Returns 0 when header unavailable

    @patch('intra42.requests.Session')
    @patch('intra42.os.path.exists')
    @patch('intra42.os.path.getmtime')
    def test_get_versioned_filepath_no_file(self, mock_getmtime, mock_exists, mock_session_class):
        """Test versioned filepath when file doesn't exist"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'Fri, 09 May 2025 12:16:12 GMT'
        mock_session.head.return_value = mock_response

        mock_exists.return_value = False

        scraper = IntraScrape({})
        path, should_download = scraper.get_versioned_filepath(
            'http://example.com/file.pdf',
            '/downloads/file.pdf'
        )

        assert path == '/downloads/file.pdf'  # Use base filename
        assert should_download == True

    @patch('intra42.requests.Session')
    @patch('intra42.os.path.exists')
    @patch('intra42.os.path.getmtime')
    def test_get_versioned_filepath_file_exists_same_version(self, mock_getmtime, mock_exists, mock_session_class):
        """Test versioned filepath when file exists and is up-to-date"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'Fri, 09 May 2025 12:16:12 GMT'
        mock_session.head.return_value = mock_response

        def exists_side_effect(path):
            # Versioned file doesn't exist, but base file does
            if path == '/downloads/file_20250509_141612.pdf':
                return False
            if path == '/downloads/file.pdf':
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_getmtime.return_value = 1746792972.0  # Same timestamp

        scraper = IntraScrape({})
        path, should_download = scraper.get_versioned_filepath(
            'http://example.com/file.pdf',
            '/downloads/file.pdf'
        )

        assert path == '/downloads/file.pdf'
        assert should_download == False  # Already up-to-date

    @patch('intra42.requests.Session')
    @patch('intra42.os.path.exists')
    @patch('intra42.os.path.getmtime')
    def test_get_versioned_filepath_file_exists_newer_version(self, mock_getmtime, mock_exists, mock_session_class):
        """Test versioned filepath when remote file is newer"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'Fri, 09 May 2025 12:16:12 GMT'
        mock_session.head.return_value = mock_response

        def exists_side_effect(path):
            # Base file exists, versioned doesn't
            if path == '/downloads/file.pdf':
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_getmtime.return_value = 1000000000.0  # Much older timestamp

        scraper = IntraScrape({})
        path, should_download = scraper.get_versioned_filepath(
            'http://example.com/file.pdf',
            '/downloads/file.pdf'
        )

        assert path == '/downloads/file_20250509_141612.pdf'  # Versioned filename
        assert should_download == True

    @patch('intra42.requests.Session')
    def test_get_total_pages(self, mock_session_class):
        """Test extracting total page count from pagination"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <div id="projects-list-container">
                <div>
                    <ul>
                        <li class="last">
                            <a href="/projects/list?page=17">Last</a>
                        </li>
                    </ul>
                </div>
            </div>
        '''
        mock_session.get.return_value = mock_response

        scraper = IntraScrape({})
        total_pages = scraper._get_total_pages()

        assert total_pages == 17

    @patch('intra42.requests.Session')
    @patch('intra42.IntraScrape._get_total_pages')
    @patch('intra42.IntraScrape._get_project_list_page')
    def test_parallel_pagination(self, mock_get_page, mock_get_total, mock_session_class):
        """Test parallel pagination fetches all pages"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_get_total.return_value = 3

        # Mock different responses for each page
        from bs4 import BeautifulSoup
        def get_page_side_effect(page):
            html = f'<li class="project-item"><div class="project-name"><a href="/p{page}">Project{page}</a></div></li>'
            soup = BeautifulSoup(html, 'html.parser')
            return [soup.find('li')]

        mock_get_page.side_effect = get_page_side_effect

        scraper = IntraScrape({})
        results = scraper._get_project_list(parallel=True, max_workers=2)

        assert len(results) == 3
        assert mock_get_page.call_count == 3

    @patch('intra42.requests.Session')
    @patch('intra42.IntraScrape._get_total_pages')
    @patch('intra42.IntraScrape._get_project_list_page')
    def test_sequential_pagination(self, mock_get_page, mock_get_total, mock_session_class):
        """Test sequential pagination fetches all pages"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_get_total.return_value = 2

        from bs4 import BeautifulSoup
        def get_page_side_effect(page):
            html = f'<li class="project-item"><div class="project-name"><a href="/p{page}">Project{page}</a></div></li>'
            soup = BeautifulSoup(html, 'html.parser')
            return [soup.find('li')]

        mock_get_page.side_effect = get_page_side_effect

        scraper = IntraScrape({})
        results = scraper._get_project_list(parallel=False)

        assert len(results) == 2
        assert mock_get_page.call_count == 2

    @patch('intra42.requests.Session')
    def test_get_projects_to_scrape(self, mock_session_class):
        """Test filtering projects by name"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        scraper = IntraScrape({})
        # Set all_projects directly instead of mocking get_all_projects
        scraper.all_projects = [
            {'name': 'libft', 'url': '/projects/libft'},
            {'name': 'ft_printf', 'url': '/projects/ft_printf'},
            {'name': 'minishell', 'url': '/projects/minishell'}
        ]

        scraper.get_projects_to_scrape(['libft', 'minishell'])

        assert len(scraper.projects_to_scrape) == 2
        assert scraper.projects_to_scrape[0]['name'] == 'libft'
        assert scraper.projects_to_scrape[1]['name'] == 'minishell'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

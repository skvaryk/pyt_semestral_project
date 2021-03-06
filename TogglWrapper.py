import json

import requests
from toggl.api_client import TogglClientApi


class ProjectNotFoundException(Exception):
    def __init__(self, message):
        self.message = message


class TogglWrapper(TogglClientApi):

    def __init__(self, api_key, user_agent, workspace_id=1):
        settings = {
            'token': api_key,
            'user_agent': user_agent,
            'workspace_id': workspace_id
        }
        super().__init__(settings)
        self.toggl_auth = (api_key, 'api_token')
        self.toggl_headers = {'Content-Type': 'application/json'}

    def get_work_spaces(self):
        response = self.get_workspaces()
        return response

    def start_time_entry(self, task_name):
        task = self.get_task_by_name(task_name)
        if task and 'id' in task:
            data = {'time_entry': {'description': task['name'], 'billable': True, 'pid': task['pid'],
                                   'created_with': 'SynePoints', 'tid': task['id']}}
            path = '/time_entries/start'
            response = self._post_query(path, dict_data=data)
            return response
        return None

    def stop_time_entry(self, task_name):
        task = self.get_task_by_name(task_name)
        current_entry = self.get_current_time_entry()
        if current_entry and task['id'] == current_entry['tid']:
            path = '/time_entries/{}/stop'.format(current_entry['id'])
            response = self._put_query(path, dict_data=None)
            return response

    def get_projects(self):
        return super().get_projects().json()

    def get_project_id_by_keyword(self, keyword):
        projects = self.get_projects()
        for project in projects:
            if keyword in project['name']:
                return project['id']
        return None

    def get_user_data(self, with_related_data='true'):
        return self._get_query(
            '/me', params={'with_related_data': with_related_data})

    def get_project_tasks(self, project_id):
        if not project_id:
            raise ValueError('Project_id cannot be None or empty. Is the project named correctly?')
        path = '/projects/{}/tasks'.format(project_id)
        return self._get_query(path)

    def get_task_by_name(self, task_name):
        task_keyword = task_name.split('-')[0] + ' '
        project_id = self.get_project_id_by_keyword(task_keyword)
        if not project_id:
            raise ProjectNotFoundException(
                'Project not found. Do you have the permission to view this toggl project?')

        tasks = self.get_project_tasks(project_id)
        for task in tasks:
            if task_name in task['name']:
                return task
        return None

    def get_current_time_entry(self):
        path = '/time_entries/current'
        response = self._get_query(path)
        return response['data']

    def get_task(self, task_id, project_id):
        tasks = self.get_project_tasks(project_id)
        for task in tasks:
            if task['id'] == task_id:
                return task
        return None

    def get_task_by_id(self, task_id):
        # this call often returns empty data - problem on toggl's side
        path = "/tasks/{}".format(task_id)
        response = self._get_query(path)
        return response['data']

    def get_current_task_key(self):
        current_time_entry = self.get_current_time_entry()
        if current_time_entry and 'tid' in current_time_entry:
            current_task = self.get_task(current_time_entry['tid'], current_time_entry['pid'])
            return current_task['name'].split(' ')[0]
        return ""

    def _post_query(self, path, dict_data):
        data = json.dumps(dict_data)
        url = self.api_base_url + path
        response = requests.post(url, headers=self.toggl_headers,
                                 auth=self.toggl_auth, data=data)
        return response.json()

    def _put_query(self, path, dict_data):
        data = json.dumps(dict_data)
        url = self.api_base_url + path
        response = requests.put(url, headers=self.toggl_headers,
                                auth=self.toggl_auth, data=data)
        return response.json()

    def _get_query(self, path, params=None):
        if params is None:
            params = {}
        return self.query(path, params=params).json()

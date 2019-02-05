from jira import JIRA


class JiraWrapper(JIRA):

    def __init__(self, server, basic_auth):
        super().__init__(server=server, basic_auth=basic_auth)

    def get_tasks_with_transitions(self):
        jira_current_user = self.current_user()
        jql = 'assignee={} AND status not in (resolved, closed) AND createdDate >= -365d'.format(jira_current_user)
        block_size = 100
        block_num = 0
        jira_tasks = []
        while True:
            start_idx = block_num * block_size
            issues = self.search_issues(jql, start_idx, block_size)
            if len(issues) == 0:
                # Retrieve issues until there are no more to come
                break
            block_num += 1
            jira_tasks.extend(issues)

        for jira_task in jira_tasks:
            transitions = self.transitions(jira_task.key)
            jira_task.transitions = transitions

        return jira_tasks

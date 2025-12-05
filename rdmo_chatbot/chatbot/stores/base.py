

class BaseStore:

    def has_history(self, user_identifier, project_id):
        raise NotImplementedError

    def get_history(self, user_identifier, project_id):
        raise NotImplementedError

    def set_history(self, user_identifier, project_id, history):
        raise NotImplementedError

    def reset_history(self, user_identifier, project_id):
        raise NotImplementedError

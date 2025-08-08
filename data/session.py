class AppSession:
    user = None
    permissions = []
    order = None
    stage = None
    csrf_token = None
    stages_cache = {}

    @classmethod
    def clear(cls):
        cls.user = None
        cls.order = None
        cls.permissions = []
        cls.stage = None
        cls.csrf_token = None
        cls.stages_cache = {}
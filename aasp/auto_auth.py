class User:
    is_superuser = True
    is_active = True
    is_staff = True
    id = 1
    pk = 1


User.has_module_perms = True
User.has_perm = True


class Middleware(object):
    def __init__(self, get_response):
         self.response = get_response
    def __call__(self, request):
        request.user = User()
        return self.response(request)
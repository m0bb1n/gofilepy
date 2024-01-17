from requests.models import Response
class GofileAPIException (Exception):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code

    @classmethod
    def __init_from_resp__ (cls, resp: Response):
        code = resp.status_code
        resp = resp.json()
        status = resp['status']

        if status == "error-auth":
            return GofileAPIAuthenticationError(status, code=code)

        elif status == "error-owner":
            return GofileAPINotOwnerError(status)

        elif status == "error-notFound":
            return GofileAPIContentNotFoundError(status)
        
        return cls(status, code) 

    def __repr__ (self):
        return "{} {} {}".format(self.__class__, self.code, self.msg)

    def __str__ (self):
        return self.__repr__()


class GofileAPIAuthenticationError (GofileAPIException):
    def __init__(self, msg: str, code: int = 401):
        super().__init__(msg, code)

class GofileAPIContentNotFoundError (GofileAPIException):
    def __init__(self, msg: str, code: int = 404):
        super().__init__(msg, code)

class GofileAPINotOwnerError (GofileAPIException):
    def __init__(self, msg: str, code: int = 403):
        super().__init__(msg, code)


from .utils import get_chainlit_token


class ChatbotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            response.set_cookie("chainlit_token", get_chainlit_token(request.user))
        else:
            if "access_token" in request.COOKIES:
                response.delete_cookie("chainlit_token")
                response.delete_cookie("access_token")
                response.delete_cookie("X-Chainlit-Session-id")

        return response

from .utils import get_chatbot_token


class ChatbotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            response.set_cookie("chatbot_token", get_chatbot_token(request.user))
        else:
            response.delete_cookie("chatbot_token")
            response.delete_cookie("access_token")
            response.delete_cookie("X-Chainlit-Session-id")

        return response

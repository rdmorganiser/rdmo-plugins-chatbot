class ChatbotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated:
            if "access_token" in request.COOKIES:
                response.delete_cookie("access_token")

        return response

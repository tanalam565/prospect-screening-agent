import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def chatbot_page(request):
    """Serves the React chatbot page."""
    return render(request, 'agent/chatbot.html')


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint that receives a message and returns the agent response."""
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        chat_history = data.get("chat_history", [])

        if not message:
            return JsonResponse({"error": "Message is required."}, status=400)

        from agent.chatbot_agent import run_chat
        response = run_chat(message, chat_history)

        return JsonResponse({"response": response})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

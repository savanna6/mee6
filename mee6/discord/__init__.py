from mee6.discord.api.client import APIClient
client_api = APIClient()

send_message = client_api.send_message
send_webhook_message = client_api.send_webhook_message

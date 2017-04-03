with open("token.txt", 'r') as f:
	BOT_TOKEN = f.read()


bot = dict(
	token = BOT_TOKEN,
	)

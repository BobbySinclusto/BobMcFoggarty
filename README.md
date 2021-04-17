# BobMcFoggarty
A Discord bot for the OSU Nerds Discord server. It has several features, including:
- Responds to math questions (using Wolfram|Alpha api): *hey bob Sum from 1 to infinity of n^2/(2n^2+1)^2*
- Searches Google when asked a question (using Google CSE api): *hey bob how do you exit vim*
- Retrieves images or animated gifs from Google Images (using Google CSE api): *hey bob animated gif of my code working*
- Knows several fun facts (scraped from [did-you-knows.com](https://did-you-knows.com)): *!funfact*

## Prerequisites
First, you need a Discord server to add Bob to. Use the name of the server as the `DISCORD_GUILD` in your `.env` file (described below)

You'll also need to create a bot using your Discord developer account. Follow [this tutorial](https://realpython.com/how-to-make-a-discord-bot-python/) up until the part where it says "How to Make a Discord Bot in Python" (that's what this is!) Copy your bot token (Bot tab -> Token) and paste it in for `DISCORD_TOKEN` in your `.env` file (described below)

Before Bob can channel the knowledge of the interwebs into his huge galaxy brain, he needs some API keys that you can get for free.
- [Wolfram|Alpha api key](https://products.wolframalpha.com/api/)
	- Use the api key you get for `WOLFRAM_API_KEY` in your `.env` file (see example `.env` below)
- [Google api key](https://developers.google.com/custom-search/v1/overview)
	- You'll need to register a custom search engine as well, following the instructions in the document. 
	- When setting up the custom search engine, it will ask for a site you want to search. It doesn't matter what you put in there, just put something.
	- Make sure that you turn on "Image search" and "Search the entire web" in the "Basics" tab of the setup menu.
	- Locate the "Search engine ID" in the "Basics" tab of the setup menu, use this for `GOOGLE_SE_ID` in your `.env` file (see example `.env` below)
	- Click the link to get an API key and use it for `GOOGLE_API_KEY` in your `.env` file (see example `.env` below)

## Installation
First, make sure all the requirements are installed:
```bash
python3 -m pip install -r requirements.txt
```

Next, create a `.env` file.
Bob uses a `.env` file to keep track of api keys and stuff. Here's an example:
```bash
DISCORD_TOKEN=this_is_not_a_real_bot_token
DISCORD_GUILD='name of your server'
WOLFRAM_API_KEY=this_is_not_a_real_api_key
GOOGLE_API_KEY=this_is_not_a_real_api_key
GOOGLE_SE_ID=custom_search_engine_id
```

For instructions on how to obtain the various api keys and stuff, see the prerequisites section.

## Running
Run the bot using
```bash
python3 bot.py
```

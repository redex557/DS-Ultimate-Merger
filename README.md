# DS Ultimate Merger Bot

A Discord bot that simplifies and automates the process of merging/combining DS-Ultimate attack plans. The bot provides an easy-to-use interface for combining multiple attack plans into a single target plan using Discord slash commands.

## Quick Start - Using the Hosted Bot

If you just want to use the bot without hosting it yourself, you can add the hosted instance to your Discord server:

1. Click this link to add the bot to your server: [Add DS Ultimate Merger Bot to your server](https://discord.com/oauth2/authorize?client_id=1314949784171184229)
2. Select the server where you want to add the bot
3. Click "Authorize" and complete the verification if prompted
4. The bot will now be available in your server with all its commands

Note: You need to have the "Manage Server" permission in the Discord server to add the bot.

## Support & Contact

If you're using the hosted instance of the bot and need help or want to report issues:
- Contact the maintainer on Discord: @notmaxxx
- Create an issue on this GitHub repository

Please provide as much detail as possible when reporting issues, including:
- The command you used
- Any error messages you received
- What you expected to happen vs what actually happened

## Features

- Merge multiple attack plans with a single command
- Save a personal default target URL
- Convenient slash commands interface
- Privacy-focused with ephemeral messages (only visible to the command user)
- URL sanitization for enhanced security

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/ds-ultimate-merger-bot
cd ds-ultimate-merger-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure the bot
   - Create a new Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
   - Copy your bot token
   - Replace the `TOKEN` variable in `merger.py` with your bot token
   - Invite the bot to your server using the OAuth2 URL generator (required permissions: bot, application.commands)

4. Run the bot
```bash
python merger.py
```

## Usage

### Available Commands

- `/merge`: Merge multiple attack plans into a target plan
  ```
  /merge target_url:<target-url> source_urls:<source-url1> <source-url2> ...
  ```

- `/set-default`: Set your personal default target URL
  ```
  /set-default url:<target-url>
  ```

- `/get-default`: Display your current default target URL
  ```
  /get-default
  ```

- `/merge-to-default`: Merge plans into your default target URL
  ```
  /merge-to-default source_urls:<source-url1> <source-url2> ...
  ```

### Example Usage

1. Merging multiple plans:
```
/merge target_url:https://ds-ultimate.de/tools/attackPlanner/123/edit/abc123 source_urls:https://ds-ultimate.de/tools/attackPlanner/123/edit/def456 https://ds-ultimate.de/tools/attackPlanner/123/edit/ghi789
```

2. Setting a default target URL:
```
/set-default url:https://ds-ultimate.de/tools/attackPlanner/123/edit/abc123
```

3. Merging into default target URL:
```
/merge-to-default source_urls:https://ds-ultimate.de/tools/attackPlanner/123/edit/def456 https://ds-ultimate.de/tools/attackPlanner/123/edit/ghi789
```

### Getting Started

1. Create a new plan on DS-Ultimate that will serve as your target plan
2. Copy the URLs of the plans you want to merge
3. Either use `/merge` directly or set up a default URL with `/set-default` and use `/merge-to-default`

## Security Features

- All sensitive parts of URLs are censored in bot responses
- Commands and responses are ephemeral (only visible to the command user)
- URL validation to ensure only valid DS-Ultimate attack planner URLs are processed
- Default URL's are stored on the server, otherwise this feature would not work. If you don't want this use the /merge command instead.

## Contributing

Feel free to submit issues and enhancement requests!

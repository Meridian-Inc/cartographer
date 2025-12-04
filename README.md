# 🗺️ Cartographer

[![Network Map](https://raw.githubusercontent.com/DevArtech/cartographer/refs/heads/main/assets/application.png)](https://cartographer.artzima.dev/embed/yJLRHFuiajaxkWvLc44Gm0f4)

> 🖱️ **[Click the image to view the interactive map](https://cartographer.artzima.dev/embed/yJLRHFuiajaxkWvLc44Gm0f4)**

**See every device on your network at a glance.**

Cartographer is a self-hosted app that maps out your home or office network. It finds all the devices, shows how they're connected, and keeps an eye on their health — so you always know what's online and what's not.

## What it does

- **Discovers your network** — Hit "Run Mapper" and watch as devices appear: routers, servers, NAS boxes, phones, smart home gadgets, you name it.
- **Drag-and-drop editing** — Rearrange the map to match how your network actually looks. Label things, group them, make it yours.
- **Health at a glance** — Green rings mean online. Red means trouble. No more guessing if your printer is down again.
- **Smart alerts** — Get notified when something goes wrong. Cartographer learns your network's normal patterns and alerts you to unusual behavior — like a device going offline unexpectedly or sudden latency spikes.
- **AI assistant** — Ask questions about your network in plain English. "What's down?" "Why is my connection slow?" Get instant answers.
- **Live updates** — See network changes in real-time as devices come online or go offline.
- **Saves your work** — Your layout is saved automatically, so you don't lose your changes.
- **Multi-user** — Set up accounts for family or teammates with different access levels.

## Getting started

You'll need [Docker](https://docs.docker.com/get-docker/) installed.

**Option 1** — Use the helper script:
```bash
./deploy.sh up
```

**Option 2** — Or run Docker Compose directly:
```bash
docker compose up --build -d
```

Then open **http://localhost:8000** in your browser.

The first time you visit, you'll create an owner account. After that, click **Run Mapper** to scan your network and start building your map!

## AI Assistant

The assistant can answer questions about your network using natural language:

- *"What devices are unhealthy?"*
- *"Show me devices with high latency"*
- *"Which devices have been offline today?"*
- *"Summarize my network health"*

To enable the assistant, you'll need to configure at least one AI provider. Copy `.example.env` to `.env` and add your API key:

```bash
cp .example.env .env
# Edit .env and add your API key (OpenAI, Anthropic, Google, or use Ollama for free local models)
```

If you run [Ollama](https://ollama.ai) locally, no API key is needed — just make sure it's running!

## Notifications

Cartographer can alert you when things go wrong on your network:

- **Device down** — Know immediately when a server, router, or important device stops responding.
- **Device recovered** — Get a heads-up when things come back online.
- **Unusual behavior** — Cartographer learns what's normal for your network and flags anything strange — like unexpected outages or performance issues.

### Notification channels

You can receive alerts via:

- **Email** — Get clean, easy-to-read emails when something needs your attention.
- **Discord** — Send alerts to a Discord channel or get direct messages from the Cartographer bot.

To set up notifications, add your credentials to the `.env` file:

```bash
# For email notifications (using Resend)
RESEND_API_KEY=your_key_here

# For Discord notifications
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id
```

Then configure your preferences in the app — choose which alerts you want, set quiet hours so you're not woken up at 3am, and pick your preferred notification channel.

## Configuration

All settings are optional and have sensible defaults. To customize, copy the example file:

```bash
cp .example.env .env
```

Then edit `.env` with your settings. See `.example.env` for all available options and descriptions.

## Tips

- **Pan mode** lets you scroll and zoom around the map.
- **Edit mode** lets you drag nodes, change their type, and rewire connections.
- Click any device to see more details and health info.
- Your changes auto-save, but you can also use **Save Map** to be sure.
- Open the **Assistant** panel and ask questions about your network in plain English.
- Set up **Notifications** to stay informed — the more Cartographer monitors your network, the smarter its alerts get.

## Need help?

- Make sure Docker is running and you're on the same network you want to map.
- The app needs elevated network permissions to scan devices — Docker Compose handles this automatically.
- **Assistant not responding?** Make sure at least one AI provider is configured in your `.env` file.
- **Not receiving notifications?** Check that your email or Discord credentials are set up correctly in `.env`, and make sure notifications are enabled in your preferences.
- For advanced setup (production deployments, custom ports, etc.), check out `deploy.sh --help`.

---

Built with FastAPI, Vue, and a lot of ping packets. 🗺️

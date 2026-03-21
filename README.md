# GitHub Copilot Bridge Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Use GitHub Copilot as a conversational AI agent inside Home Assistant. Talk to it via voice assistants, automations, or the HA chat UI.

## Credits

Built on top of the original work by [@tserra30](https://github.com/tserra30) at [tserra30/Github-Copilot-SDK-integration](https://github.com/tserra30/Github-Copilot-SDK-integration). Many thanks for laying the foundation that made this possible.

## How it works

This project has two parts that work together:

1. **GitHub Copilot Bridge Addon** — installs the Copilot CLI binary in a dedicated container and runs it in server mode on port 7681 (internal Supervisor network only)
2. **GitHub Copilot Bridge Integration** — a custom HA integration that connects to the addon over the internal network and exposes a conversation agent

The integration never touches your GitHub token — authentication is handled entirely by the add-on.

## Requirements

- Home Assistant OS or Supervised (the add-on requires the Supervisor)
- A GitHub account with an active [Copilot subscription](https://github.com/features/copilot)
- A GitHub Personal Access Token with Copilot permissions

## Setup

Install in this order: **add-on first, then integration**.

### 1. Install the GitHub Copilot Bridge Addon

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Click **⋮** (top-right) → **Repositories**
3. Add: `https://github.com/tserra30/Github-Copilot-SDK-integration`
4. Find **GitHub Copilot Bridge Addon** and click **Install**
5. Open the add-on **Configuration** tab and fill in your token and port:
   ```yaml
   github_token: "ghp_yourTokenHere"
   port: 7681
   ```
6. Click **Start**, then open the **Log** tab and confirm you see:
   ```
   GitHub Copilot Bridge Add-on Starting
   Copilot CLI version: ...
   Starting Copilot CLI in server mode on port 7681 (attempt 1/5)...
   ```

> **Getting a token**: Go to [GitHub Settings → Tokens](https://github.com/settings/tokens), create a Personal Access Token, and make sure your account has an active Copilot subscription.

### 2. Install the GitHub Copilot Bridge Integration

**Via HACS (recommended)**

1. Open HACS → **Integrations** → click **+**
2. Search for **GitHub Copilot Bridge Integration** and install it
3. Restart Home Assistant

**Manual**

1. Copy the `custom_components/github_copilot` directory into your HA `custom_components` folder
2. Restart Home Assistant

### 3. Configure the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **GitHub Copilot Bridge Integration**
3. The **Add-on URL** field is pre-filled with `http://github-copilot-bridge:7681` — this is the fixed hostname set in the add-on
4. Select a **Model** (default: `gpt-4o`)
5. Click **Submit** — the integration will test the connection to the running add-on

> If the URL doesn't work, check the add-on **Info** tab for the actual hostname. It will look something like `56b5df53-github-copilot-bridge` (a hex prefix + your slug). Use `http://<hostname>:7681`.

## Usage

### Conversation agent

Once set up, select **GitHub Copilot Bridge Integration** as the conversation agent in:
- A voice assistant pipeline (**Settings** → **Voice Assistants**)
- The HA chat UI

### Automation example

```yaml
automation:
  - alias: "Ask Copilot for a morning summary"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: conversation.process
        data:
          text: "Good morning! Give me a quick summary of what I should know today."
          agent_id: conversation.github_copilot
```

### Changing the model

Go to **Settings** → **Devices & Services** → **GitHub Copilot Bridge Integration** → **Configure** to switch models.

| Model | Cost (paid plans) | Notes |
|---|---|---|
| `gpt-4o` ✓ | **Included** | Default. Best balance of quality and speed |
| `gpt-4o-mini` ✓ | **Included** | Faster, lighter — good for quick tasks |
| `gpt-3.5-turbo` ✓ | **Included** | Fastest, lowest quality |
| `o3-mini` | Premium | Reasoning model — slower, very capable |
| `o1-mini` | Premium | Reasoning model |
| `o1` | Premium (high) | Deep reasoning, high token cost |
| `gpt-4-turbo` | Premium | Strong quality, premium cost |
| `gpt-4` | Premium | Older flagship model |
| `claude-3.5-sonnet` | Premium (~1×) | Anthropic model |
| `claude-3.7-sonnet` | Premium (~1×) | Anthropic model, latest |

> **Tip:** Start with `gpt-4o` — it's included in paid plans, so every request is free against your allowance. Switch to a premium model only if you need deeper reasoning or a specific style. GitHub updates multipliers frequently; check [github.com/features/copilot/plans](https://github.com/features/copilot/plans) for current numbers.

## Troubleshooting

**Check the add-on Log tab first** — it logs the CLI version, each startup attempt, and every line of output from the Copilot process (prefixed with `[copilot]`). Then check **Settings** → **System** → **Logs** for integration-level errors.

| Symptom | Check |
|---|---|
| Add-on fails to start (exit code non-zero) | Add-on logs — look for the `[copilot]` lines showing the exact error |
| "Connection refused" in HA logs | Is the add-on running? Is the URL/port correct? |
| "Protocol version mismatch" in HA logs | Update the integration — the SDK version must match the CLI. Delete and re-add the integration after updating. |
| "Add-on URL" field — wrong hostname | The add-on uses the fixed hostname `github-copilot-bridge`. Use `http://github-copilot-bridge:7681` |
| "Authentication failed" | Is the `github_token` in add-on config valid? Does the account have a Copilot subscription? |
| Integration setup fails with "connection" error | Start the GitHub Copilot Bridge Addon before setting up the integration |
| Empty or no response | Check GitHub service status; try again |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the GNU GPLv3 — see [LICENSE](LICENSE) for details.
Some source code was originally licensed under the MIT License.

This integration depends on the [GitHub Copilot SDK](https://github.com/github/copilot-cli), licensed under the MIT License.

**This project is not officially affiliated with GitHub or Microsoft.**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/tserra30/Github-Copilot-SDK-integration.svg?style=for-the-badge
[commits]: https://github.com/tserra30/Github-Copilot-SDK-integration/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/tserra30/Github-Copilot-SDK-integration.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/tserra30/Github-Copilot-SDK-integration.svg?style=for-the-badge
[releases]: https://github.com/tserra30/Github-Copilot-SDK-integration/releases
[issues]: https://github.com/tserra30/Github-Copilot-SDK-integration/issues


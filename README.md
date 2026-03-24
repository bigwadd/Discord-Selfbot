```markdown
# Waddle's-SELFbot


A Discord selfbot framework with automation tools, status management, cryptocurrency utilities, and user intelligence features.

---

## Liability Notice

**Use at your own risk.** Discord selfbots violate the Terms of Service. The author assumes no responsibility for account terminations, data loss, or service restrictions. Test thoroughly on alternate accounts before any production use. By running this software, you accept full liability for any consequences.

---

## Features

### Core Utilities
| Command | Description |
|---------|-------------|
| `.react <emoji>` / `.react off` | Auto-react to all messages |
| `.ping` | Latency check |
| `.msgdelete <count>` | Bulk delete own messages |
| `.rpc <state> \| <details> \| <image>` | Custom Rich Presence |
| `.gif` | Convert images to GIF format |

### Status Control
| Command | Description |
|---------|-------------|
| `.online` / `.idle` / `.dnd` / `.invisible` | Set presence status |
| `.statusrotate add <text>` | Add rotating status |
| `.statusrotate remove <index>` | Remove status by index |
| `.statusrotate list` | View rotation queue |
| `.statusrotate on/off` | Toggle rotation |
| `.statusrotate mode <status>` | Set rotation base status |

### User Intelligence
| Command | Description |
|---------|-------------|
| `.avatar [@user]` | Retrieve avatar URL |
| `.userinfo [@user]` | Guild-specific user data |
| `.whois [@user]` | Account metadata and flags |
| `.id [target]` | Resolve IDs for users/channels/roles/server |

### Cryptocurrency Tools
| Command | Description |
|---------|-------------|
| `.track <address>` | Wallet balance lookup (BTC, ETH, LTC, DOGE) |
| `.price <currency>` | Current market price |
| `.convert <amount> <from> <to>` | Cross-currency conversion |

Supported currencies: `btc`, `eth`, `ltc`, `xrp`, `usdt`, `usdc`, `doge`

### System Utilities
| Command | Description |
|---------|-------------|
| `.tokeninfo <token>` | Token metadata decoder |
| `.iplook <address>` | IP geolocation data |
| `.stats` | Process and system metrics |

### AFK System
| Command | Description |
|---------|-------------|
| `.afk [reason]` | Enable AFK with auto-reply |
| `.unafk` | Disable AFK |

### Automation
| Command | Description |
|---------|-------------|
| `.addar <trigger> <response>` | Create auto-response |
| `.delar <trigger>` | Remove auto-response |
| `.listar` | View all auto-responses |
| `.startauto <sec> <repeat> <#channel> <msg>` | Scheduled messaging |
| `.listauto` | View active auto-messages |
| `.stopauto <id>` | Terminate auto-message task |

---

## Installation

### Requirements
- Python 3.8 or higher
- pip package manager

### Dependencies
```bash
pip install discord.py aiohttp psutil pillow requests
```

Note: `discord.py` v1.7.3 or the `discord.py-self` fork is required for selfbot functionality. Standard v2.0+ does not support user account automation.

### Configuration
1. Open `bot.py`
2. Locate the `TOKEN` variable at line 25
3. Replace with your Discord user token
4. Adjust `PREFIX` if desired (default: `.`)

### Execution
```bash
python bot.py
```

---

## Technical Details

### Data Persistence
The bot maintains JSON databases for state management:
- `afk_data.json` — AFK status and reasons
- `auto_responses.json` — Trigger-response pairs
- `auto_messages.json` — Scheduled message configurations
- `status_rotation.json` — Status rotation queue

### API Integrations
- **CoinGecko** — Cryptocurrency pricing data
- **BlockCypher** — Blockchain address queries
- **ipgeolocation.io** — IP intelligence

### Architecture
- Async/await pattern via `asyncio`
- ThreadPoolExecutor for blocking operations
- Selfbot flag enabled (`self_bot=True`)
- Command extension framework

---

## Command Reference

### Syntax Conventions
- `<parameter>` — Required argument
- `[parameter]` — Optional argument
- `|` — Parameter separator (for multi-part commands)
- `@user` — Discord mention or ID

### Examples

```
.statusrotate add coding in python
.track 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
.tokeninfo NzQ1O...
.startauto 60 true #general server announcement
```

---

## Security Considerations

1. **Token Exposure** — Hardcoded tokens in source files present security risks. Consider environment variables for production deployments.
2. **Rate Limiting** — Discord implements aggressive rate limits on user accounts. The bot includes basic delays but does not implement comprehensive backoff strategies.
3. **Detection Vectors** — Rapid message deletion, consistent reaction timing, and automated status changes may trigger anti-abuse systems.

---
## License

GNU General Public License v3.0 (GPL-3.0)

This software is free and open source. You may use, modify, and distribute it freely. Commercial sale of this software or derivative works is prohibited. All derivative works must be distributed under the same license terms. See LICENSE file for full details.

---

## Acknowledgments

Developed by @pissvad

Terry A. Davis memorial quotes included via `.terryquote`

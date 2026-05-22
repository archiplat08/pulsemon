# pulsemon

Minimal self-hosted uptime monitor with alerting via webhook and email, backed by SQLite.

---

## Installation

```bash
pip install pulsemon
```

Or clone and install locally:

```bash
git clone https://github.com/yourname/pulsemon.git && cd pulsemon && pip install -e .
```

---

## Usage

Create a `config.yml` file:

```yaml
checks:
  - name: My API
    url: https://api.example.com/health
    interval: 60

alerts:
  email:
    to: you@example.com
    smtp_host: smtp.example.com
  webhook:
    url: https://hooks.slack.com/services/your/webhook/url
```

Start the monitor:

```bash
pulsemon start --config config.yml
```

View status in your terminal:

```bash
pulsemon status
```

All check history is stored in a local SQLite database (`pulsemon.db`) in the working directory.

---

## Features

- Monitors HTTP/HTTPS endpoints at configurable intervals
- Sends alerts via email and/or webhook on status changes
- Lightweight SQLite backend — no external database required
- Simple YAML configuration

---

## License

MIT © 2024 yourname
def format_markdown_note(title: str, created, body: str) -> str:
    timestamp = created.strftime("%Y-%m-%dT%H:%M:00")
    return f"""---
Title: "{title}"
Created: {timestamp}
ReviewAt: 
Deadline: 
tags:
  - simpledocument
  - kanbancard
aliases: 
Domajnoj:
  - "[[El Telegram]]"
---
## Detaloj
{body}
"""

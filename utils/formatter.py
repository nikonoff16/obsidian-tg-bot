from datetime import datetime


def format_markdown_note(title: str, created: datetime, body: str, forwarded_from: str = None) -> str:
    front = [
        f'Title: "{title}"',
        f"Created: {created.strftime('%Y-%m-%dT%H:%M:%S')}",
        "ReviewAt:",
        "Deadline:",
        "tags:",
        "  - simpledocument",
        "  - kanbancard",
        "aliases:"
    ]
    if forwarded_from:
        front.append(f'ForwardedFrom: "{forwarded_from}"')
    front.append('Domajnoj:\n  - "[[El Telegram]]"')

    return f"---\n" + "\n".join(front) + "\n---\n## Detaloj\n" + body
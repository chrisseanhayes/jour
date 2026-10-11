import ast
import re
from typing import List, Tuple


_HASHTAG_PATTERN = re.compile(r"(?<![\w#])#([\w]+(?:-[\w]+)*)(?![\w-])")


def _extract_hashtags(text: str) -> List[str]:
    """Extract whole-word hashtags without their leading hash symbol."""
    return list(dict.fromkeys(_HASHTAG_PATTERN.findall(text)))


def _build_note_content(
    layout: str,
    date_str: str,
    tags: List[str],
    note_body: str,
) -> str:
    """Construct the markdown content with YAML front matter."""
    return f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
tags: {tags}
---

{note_body}
"""


def _parse_note_content(content: str) -> Tuple[List[str], str]:
    """Parse front-matter tags and body from note content."""
    parts = content.split("---", 2)
    tags = []
    body = ""
    if len(parts) >= 3:
        front_matter = parts[1]
        body = parts[2].strip()
        for line in front_matter.split("\n"):
            if line.startswith("tags: "):
                tags_str = line[len("tags: "):].strip()
                try:
                    tags = ast.literal_eval(tags_str)
                except:
                    pass
    else:
        body = content.strip()
    return list(dict.fromkeys(tags + _extract_hashtags(body))), body


def _has_note_body(content: str) -> bool:
    """Return whether note content has a non-empty body after front matter."""
    _, body = _parse_note_content(content)
    return bool(body)


def _get_body_preview(body: str, max_length: int = 40) -> str:
    """Generate a single-line truncated preview of the note body."""
    body_preview = body.replace("\n", " ")
    if len(body_preview) > max_length:
        body_preview = body_preview[:max_length - 3] + "..."
    return body_preview

import sys
from enum import Enum
from typing import Optional

from django.http import HttpRequest


class TabEnum(Enum):
    do_not_call_in_templates = True
    MOST_VIEWED = "mostviewed"
    UNANSWERED = "unanswered"
    LATEST = "latest"
    UNRESOLVED = "unresolved"


def _find_code_blocks(markdown_text_lines: list[str]) -> list[tuple[int, int]]:
    res: list[tuple[int, int]] = list()
    start = None
    for i, line in enumerate(markdown_text_lines):
        if "```" in line:
            if start is None:
                start = i
            else:
                res.append((start, i))
                start = None
    return res


def _dedent_code_block(lines: list[str], start: int, end: int) -> None:
    fence_start = lines[start].find("```")
    line_start = sys.maxsize
    for i in range(start + 1, end):
        line_start = min(line_start, len(lines[i]) - len(lines[i].lstrip()))
    line_start = max(line_start, 0)
    dedent_chars = line_start - fence_start
    if dedent_chars == 0:
        return
    for i in range(start + 1, end):
        lines[i] = lines[i][dedent_chars:]


def dedent_code(markdown_text: str) -> str:
    """Dedent all code blocks in markdown_text"""
    lines = markdown_text.split("\n")
    code_blocks_sections = _find_code_blocks(lines)
    for section in code_blocks_sections:
        _dedent_code_block(lines, section[0], section[1])
    return "\n".join(lines)


def get_request_param(request: HttpRequest, param_name: str, default_value: Optional[str]) -> Optional[str]:
    """Get a parameter value from a request"""
    if request.GET:
        return request.GET.get(param_name, default_value)  # type: ignore
    return default_value


def get_request_tab(request: HttpRequest):
    res = get_request_param(request, "tab", "latest")
    return res if res in {tab.value for tab in TabEnum} else TabEnum.LATEST


__all__ = [
    "get_request_tab",
    "get_request_param",
    "dedent_code",
    "TabEnum",
]

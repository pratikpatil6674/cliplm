"""Safe text previews for HTML clipboard entries."""

from html.parser import HTMLParser


class _HTMLPreviewParser(HTMLParser):
    """Extract visible text without asking Qt to load embedded resources."""

    _BLOCK_TAGS = {
        "address", "article", "blockquote", "br", "div", "footer", "h1", "h2",
        "h3", "h4", "h5", "h6", "header", "li", "main", "ol", "p", "pre",
        "section", "table", "tr", "ul",
    }
    _HIDDEN_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._HIDDEN_TAGS:
            self._hidden_depth += 1
        elif not self._hidden_depth and tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._HIDDEN_TAGS and self._hidden_depth:
            self._hidden_depth -= 1
        elif not self._hidden_depth and tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            self._parts.append(data)

    def text(self) -> str:
        lines = (" ".join(line.split()) for line in "".join(self._parts).splitlines())
        return "\n".join(line for line in lines if line)


def html_preview_text(value: str) -> str:
    """Return readable HTML text without decoding images or other resources."""
    parser = _HTMLPreviewParser()
    try:
        parser.feed(value or "")
        parser.close()
    except Exception:
        # A clipboard preview may end halfway through an HTML tag. HTMLParser is
        # tolerant, but retain already extracted text if unusual markup fails.
        pass
    return parser.text()

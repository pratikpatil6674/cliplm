import tomllib
from pathlib import Path



class PromptsStore:
    """Persist named AI prompts in a human-editable TOML file.

    Prompt data is represented as ``{name: {"prompt": text, ...}}``. The store
    loads eagerly so callers can read ``prompt_config`` immediately. A missing
    file is treated as an empty store, while parse and I/O failures are exposed
    through ``last_error`` for the UI to report.
    """

    def __init__(self, store_path):
        """Create a store for ``store_path`` and immediately load its contents."""
        self.store_path = store_path
        self.last_error = None
        self.load_prompts()

    def load_prompts(self):
        """Load and normalize prompts, retaining errors instead of raising them.

        The application can start without a prompts file, so absence is not an
        error. Invalid TOML and other read failures clear the in-memory config
        and populate ``last_error`` for the Agent tab to display.
        """
        try:
            with open(self.store_path, "rb") as f:
                self.prompt_config = self._normalize_prompt_config(tomllib.load(f))
                self.last_error = None
        except FileNotFoundError:
            print(f"{self.store_path} not found")
            self.prompt_config = {}
            self.last_error = None
        except Exception as e:
            print(f"Error loading prompts: {e}")
            self.prompt_config = {}
            self.last_error = str(e)

    def save_prompts(self, prompt_config):
        """Normalize and replace the in-memory and on-disk prompt config.

        Parent directories are created on demand. The in-memory value is only
        updated after the file write succeeds, keeping it consistent with what
        was persisted.
        """
        store_path = Path(self.store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_config = self._normalize_prompt_config(prompt_config)
        toml_text = self._serialize_prompt_config(normalized_config)
        store_path.write_text(toml_text, encoding="utf-8")
        self.prompt_config = normalized_config
        self.last_error = None

    def _normalize_prompt_config(self, prompt_config):
        """Remove trailing line breaks without changing internal paragraphs.

        Older serialization placed a newline before a multiline TOML string's
        closing delimiter. TOML preserves that newline as prompt content, which
        produced invisible blank lines in the editor and an oversized preview.
        Non-dictionary entries are retained so validation remains the UI's job.
        """
        normalized_config = {}
        for prompt_name, value in prompt_config.items():
            if not isinstance(value, dict):
                normalized_config[prompt_name] = value
                continue

            prompt_data = dict(value)
            prompt_data["prompt"] = str(prompt_data.get("prompt", "")).rstrip(
                "\r\n"
            )
            normalized_config[prompt_name] = prompt_data
        return normalized_config

    def _serialize_prompt_config(self, prompt_config):
        """Serialize prompts as one quoted TOML table per prompt name.

        TOML discards the newline immediately after an opening triple quote.
        The closing delimiter is therefore kept directly after the prompt text
        so serialization does not introduce a trailing newline into the value.
        """
        sections = []
        for prompt_name, value in prompt_config.items():
            prompt_body = str(value.get("prompt", ""))
            escaped_name = self._escape_toml_string(str(prompt_name))
            escaped_prompt = self._escape_toml_multiline(prompt_body)
            sections.append(
                f'["{escaped_name}"]\n'
                f'prompt = """\n{escaped_prompt}"""\n'
            )

        return "\n".join(sections)

    def _escape_toml_string(self, value):
        """Escape a value used inside a double-quoted TOML table name."""
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _escape_toml_multiline(self, value):
        """Prevent prompt content from terminating its multiline TOML string."""
        return value.replace('"""', '\\"""')

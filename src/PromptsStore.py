import tomllib
from pathlib import Path



class PromptsStore:
    def __init__(self, store_path):
        self.store_path = store_path
        self.last_error = None
        self.load_prompts()
    
    def load_prompts(self):
        try:
            with open(self.store_path, "rb") as f:
                self.prompt_config = tomllib.load(f)
                self.last_error = None
                print("Loaded prompts:", self.prompt_config)
        except FileNotFoundError:
            print(f"{self.store_path} not found")
            self.prompt_config = {}
            self.last_error = None
        except Exception as e:
            print(f"Error loading prompts: {e}")
            self.prompt_config = {}
            self.last_error = str(e)

    def save_prompts(self, prompt_config):
        store_path = Path(self.store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)
        toml_text = self._serialize_prompt_config(prompt_config)
        store_path.write_text(toml_text, encoding="utf-8")
        self.prompt_config = prompt_config
        self.last_error = None

    def _serialize_prompt_config(self, prompt_config):
        sections = []
        for prompt_name, value in prompt_config.items():
            prompt_body = str(value.get("prompt", ""))
            escaped_name = self._escape_toml_string(str(prompt_name))
            escaped_prompt = self._escape_toml_multiline(prompt_body)
            sections.append(
                f'["{escaped_name}"]\n'
                f'prompt = """\n{escaped_prompt}\n"""\n'
            )

        return "\n".join(sections)

    def _escape_toml_string(self, value):
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _escape_toml_multiline(self, value):
        return value.replace('"""', '\\"""')

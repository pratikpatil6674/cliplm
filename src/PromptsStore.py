
import tomllib



class PromptsStore:
    def __init__(self, store_path):
        self.store_path = store_path
        self.load_prompts()
    
    def load_prompts(self):
        try:
            with open(self.store_path, "rb") as f:
                self.prompt_config = tomllib.load(f)
                print("Loaded prompts:", self.prompt_config)
        except FileNotFoundError:
            print(f"{self.store_path} not found")
            self.prompt_config = {}
        except Exception as e:
            print(f"Error loading prompts: {e}")
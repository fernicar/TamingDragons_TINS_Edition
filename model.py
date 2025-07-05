import json
import os
from pathlib import Path
import re
from typing import Dict, Any, Tuple, List

class TamingDragonsModel:
    def __init__(self):
        self.base_config: Dict[str, Any] = {}
        self.comparison_config: Dict[str, Any] = {}
        self.working_config: Dict[str, Any] = {}

        self.daily_tweaks_map: Dict[str, str] = {
            'output_name': 'Output Name',
            'training_comment': 'Training Comment (Trigger Words)',
            'sample_prompts': 'Sample Prompts',
            'learning_rate': 'Learning Rate',
            'unet_lr': 'UNet Learning Rate',
            'text_encoder_lr': 'Text Encoder Learning Rate',
            'epoch': 'Epochs',
            'max_train_steps': 'Max Train Steps',
            'seed': 'Seed',
            'train_batch_size': 'Batch Size'
        }

        self.important_params_map: Dict[str, str] = {
            'optimizer': 'Optimizer',
            'lr_scheduler': 'LR Scheduler',
            'network_dim': 'Network Dimension',
            'network_alpha': 'Network Alpha',
            'noise_offset': 'Noise Offset',
            'min_snr_gamma': 'Min SNR Gamma',
            'save_every_n_epochs': 'Save Every N Epochs',
            'save_every_n_steps': 'Save Every N Steps'
        }

    def load_config_file(self, file_path: str) -> Tuple[Dict[str, Any], str]:
        """Loads a JSON configuration file and returns config dict + status message."""
        try:
            if not file_path or not os.path.exists(file_path):
                return {}, "No file selected or file does not exist."

            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            config_type = "Unknown"
            if config.get('LoRA_type') == 'Flux1':
                config_type = "Flux1 LoRA"
            elif config.get('sdxl', False):
                config_type = "SDXL LoRA"
            elif config.get('LoRA_type') == 'Standard':
                config_type = "Standard LoRA"

            optimizer = config.get('optimizer', 'Unknown')

            return config, f"✅ Loaded {config_type} config using {optimizer} optimizer"

        except Exception as e:
            return {}, f"❌ Error loading file: {str(e)}"

    def set_base_config(self, file_path: str) -> Tuple[str, Dict[str, str]]:
        """Loads the base configuration, sets working_config, and returns status and daily tweak values."""
        if not file_path:
            return "Select a base configuration file", {}

        config, status = self.load_config_file(file_path)

        if not config:
            return status, {}

        self.base_config = config
        self.working_config = self.base_config.copy() # Important: make a copy

        daily_tweak_values: Dict[str, str] = {}
        for param_key in self.daily_tweaks_map.keys():
            value = self.working_config.get(param_key)
            daily_tweak_values[param_key] = str(value) if value is not None else ""

        return status, daily_tweak_values

    def compare_loaded_configs(self, comp_file_path: str) -> str:
        """Compares the current base_config with another config file."""
        if not self.base_config:
            return "Please load a base configuration first for comparison."
        if not comp_file_path:
            return "Please select a comparison configuration file."

        comparison_config, comp_status = self.load_config_file(comp_file_path)

        if not comparison_config:
            return f"Error loading comparison file:\n{comp_status}"

        self.comparison_config = comparison_config # Store for potential future use

        # Generate comparison
        comparison_parts = []
        # Assuming base_config status was already shown when loaded.
        # We can re-generate it if needed, or store it. For now, let's assume it's known.
        # _, base_status = self.load_config_file(self.base_config_path) # if base_config_path is stored

        base_status_type = "Unknown"
        if self.base_config.get('LoRA_type') == 'Flux1': base_status_type = "Flux1 LoRA"
        elif self.base_config.get('sdxl', False): base_status_type = "SDXL LoRA"
        elif self.base_config.get('LoRA_type') == 'Standard': base_status_type = "Standard LoRA"
        base_optimizer = self.base_config.get('optimizer', 'Unknown')
        base_full_status = f"Base: {base_status_type} config using {base_optimizer} optimizer"

        comparison_parts.append("## 🔍 Configuration Comparison")
        comparison_parts.append(f"**{base_full_status}**")
        comparison_parts.append(f"**Comparison:** {comp_status}") # comp_status from load_config_file

        daily_diffs = []
        for param, label in self.daily_tweaks_map.items():
            base_val = self.base_config.get(param, "Not set")
            comp_val = self.comparison_config.get(param, "Not set")

            if str(base_val) != str(comp_val): # Compare as strings for simplicity here
                daily_diffs.append(f"**{label}:**\n  Base: `{base_val}`\n  Comparison: `{comp_val}`")

        if daily_diffs:
            comparison_parts.append("\n### 📝 Daily Tweaks Differences")
            comparison_parts.extend(daily_diffs)

        important_diffs = []
        for param, label in self.important_params_map.items():
            base_val = self.base_config.get(param, "Not set")
            comp_val = self.comparison_config.get(param, "Not set")

            if str(base_val) != str(comp_val):
                important_diffs.append(f"**{label}:** `{base_val}` → `{comp_val}`")

        if important_diffs:
            comparison_parts.append("\n### ⚙️ Important Parameter Differences")
            comparison_parts.extend(important_diffs)

        # Check optimizer args (only if optimizer is the same, or always show if different)
        base_opt = self.base_config.get('optimizer', '')
        comp_opt = self.comparison_config.get('optimizer', '')

        # Optimizer specific checks (optimizer key is in important_params, so covered above if different)
        # Here we focus on optimizer_args
        base_args = self.base_config.get('optimizer_args', None) # Use None to distinguish from empty string
        comp_args = self.comparison_config.get('optimizer_args', None)

        if base_args != comp_args : # Handles None vs string, string vs string
            comparison_parts.append(f"\n### 🔧 Optimizer Arguments Changed:")
            comparison_parts.append(f"Base Args: `{base_args if base_args is not None else 'Not set'}`")
            comparison_parts.append(f"Comparison Args: `{comp_args if comp_args is not None else 'Not set'}`")

        if not daily_diffs and not important_diffs and base_args == comp_args:
             # Check if optimizer itself was different (already covered by important_diffs)
            if base_opt == comp_opt:
                comparison_parts.append("\n✅ **Configurations are very similar in key parameters!**")
            else: # Optimizers were different but no other key diffs
                comparison_parts.append("\n⚠️ **Optimizers differ, but other key parameters are similar.**")


        return "\n\n".join(comparison_parts)

    def update_working_config_daily_tweaks(self, new_values: Dict[str, str]) -> str:
        """Updates the working configuration with new daily tweak values."""
        if not self.working_config:
            return "❌ Please load a base configuration first"

        updated_params_count = 0
        for param_key, str_value in new_values.items():
            if param_key not in self.daily_tweaks_map:
                continue # Should not happen if new_values keys are from daily_tweaks_map

            if str_value.strip() or isinstance(self.working_config.get(param_key), bool): # Update if not empty OR if original is bool (empty string might mean False)
                original_val = self.working_config.get(param_key)

                try:
                    if isinstance(original_val, bool):
                        new_typed_value = str_value.lower() in ('true', '1', 'yes', 'on', 'checked')
                    elif isinstance(original_val, int):
                        new_typed_value = int(str_value)
                    elif isinstance(original_val, float):
                        new_typed_value = float(str_value)
                    else: # Includes strings, None, or types not explicitly handled
                        new_typed_value = str_value

                    self.working_config[param_key] = new_typed_value
                    updated_params_count +=1
                except ValueError:
                    # If conversion fails for int/float, store as string as a fallback
                    self.working_config[param_key] = str_value
                    updated_params_count +=1

        if updated_params_count > 0:
            return f"✅ Daily tweaks updated successfully ({updated_params_count} parameters changed)."
        else:
            return "ℹ️ No changes applied to daily tweaks (values were empty or same)."


    def get_working_config_summary_markdown(self) -> str:
        """Returns a markdown formatted string summary of the current working configuration."""
        if not self.working_config:
            return "No configuration loaded. Please load a base config first."

        summary_parts = []
        summary_parts.append("## 🎯 Current Configuration Summary")

        summary_parts.append("\n### Daily Tweaks")
        for param, label in self.daily_tweaks_map.items():
            value = self.working_config.get(param, "Not set")
            summary_parts.append(f"- **{label}:** `{value}`")

        summary_parts.append("\n### Key Settings (Important Parameters)")
        for param, label in self.important_params_map.items():
            value = self.working_config.get(param, "Not set")
            summary_parts.append(f"- **{label}:** `{value}`")

        # Optionally, add other specific sections if needed, e.g., optimizer_args if not in important_params
        opt_args = self.working_config.get('optimizer_args')
        if opt_args is not None: # Check for None explicitly
             summary_parts.append(f"- **Optimizer Args:** `{opt_args}`")
        else:
             summary_parts.append(f"- **Optimizer Args:** `Not set`")


        return "\n".join(summary_parts)

    def save_working_config(self, filename: str) -> str:
        """Saves the working configuration to a JSON file."""
        if not self.working_config:
            return "❌ No configuration to save."

        try:
            if not filename.strip():
                return "❌ Filename cannot be empty."

            # Ensure .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'

            save_dir = Path("configs")
            save_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists

            save_path = save_dir / filename

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.working_config, f, indent=2, ensure_ascii=False)

            return f"✅ Configuration saved successfully as: {save_path.resolve()}"

        except Exception as e:
            return f"❌ Error saving configuration: {str(e)}"

    def suggest_filename(self) -> str:
        """Generates a filename suggestion based on current working_config."""
        if not self.working_config:
            return "modified_config.json"

        output_name = self.working_config.get('output_name', "")
        training_comment = self.working_config.get('training_comment', "")

        base_name_part = ""
        if output_name:
            base_name_part = str(output_name)
        elif training_comment:
            # Extract first two words from training_comment
            words = str(training_comment).split()[:2]
            # Sanitize each word: remove non-alphanumeric characters (allow underscore and hyphen)
            # then join them
            sanitized_words = [re.sub(r'[^\w-]', '', word) for word in words]
            base_name_part = '_'.join(filter(None, sanitized_words)) # Filter out empty strings after sanitization

        if not base_name_part: # If still empty after trying output_name and training_comment
            base_name_part = "modified"

        # Sanitize the derived base_name_part (again, to catch cases from output_name directly)
        # Allow letters, numbers, underscore, hyphen. Replace others with underscore.
        sanitized_base = re.sub(r'[^\w\-_]', '_', base_name_part)

        return f"{sanitized_base}_config.json"

# Example of how to use the model (for testing or direct script use)
if __name__ == "__main__":
    model = TamingDragonsModel()

    # Test loading a dummy config (create a dummy test_config.json)
    dummy_config_content = {
        "output_name": "TestLoRA_v1",
        "training_comment": "testlora character",
        "sample_prompts": "testlora character, high quality",
        "learning_rate": 0.0001,
        "unet_lr": 0.0001,
        "text_encoder_lr": 5e-5,
        "epoch": 10,
        "max_train_steps": 1000,
        "seed": 1234,
        "train_batch_size": 1,
        "optimizer": "AdamW",
        "lr_scheduler": "cosine",
        "network_dim": 128,
        "network_alpha": 64,
        "noise_offset": 0.0,
        "min_snr_gamma": 5.0,
        "save_every_n_epochs": 1,
        "save_every_n_steps": 0,
        "sdxl": True,
        "LoRA_type": "Standard",
        "optimizer_args": None
    }
    dummy_config_path = Path("test_config.json")
    with open(dummy_config_path, 'w') as f:
        json.dump(dummy_config_content, f, indent=2)

    print("--- Testing Load Base Config ---")
    status, tweaks = model.set_base_config(str(dummy_config_path))
    print(f"Status: {status}")
    if tweaks:
        print("Daily Tweaks Loaded:")
        for k, v in tweaks.items():
            print(f"  {k}: {v}")
    print(f"Working config after load: {model.working_config.get('output_name')}")

    print("\n--- Testing Suggest Filename (initial) ---")
    print(f"Suggested: {model.suggest_filename()}") # Expected: TestLoRA_v1_config.json

    print("\n--- Testing Update Daily Tweaks ---")
    new_daily_values = {
        "output_name": "MyUpdatedLoRA",
        "learning_rate": "0.0002",
        "epoch": "15",
        "sample_prompts": "updated prompts here" # Test multiline
    }
    update_status = model.update_working_config_daily_tweaks(new_daily_values)
    print(f"Update Status: {update_status}")
    print(f"Working config 'output_name' after update: {model.working_config.get('output_name')}")
    print(f"Working config 'learning_rate' after update: {model.working_config.get('learning_rate')}")
    print(f"Working config 'epoch' after update: {model.working_config.get('epoch')}")
    print(f"Working config 'sample_prompts' after update: {model.working_config.get('sample_prompts')}")


    print("\n--- Testing Suggest Filename (after update) ---")
    print(f"Suggested: {model.suggest_filename()}") # Expected: MyUpdatedLoRA_config.json

    print("\n--- Testing Get Working Config Summary ---")
    summary = model.get_working_config_summary_markdown()
    print(summary)

    print("\n--- Testing Save Config ---")
    save_filename = model.suggest_filename()
    save_status = model.save_working_config(save_filename)
    print(f"Save Status: {save_status}")
    if "✅" in save_status:
        print(f"Config saved to configs/{save_filename}. Check its content.")

    # Test comparison
    dummy_comp_config_content = dummy_config_content.copy()
    dummy_comp_config_content["learning_rate"] = 0.0005
    dummy_comp_config_content["optimizer"] = "AdamW8bit"
    dummy_comp_config_content["network_dim"] = 32
    dummy_comp_config_content["optimizer_args"] = ["betas=0.9,0.99"]


    comp_config_path = Path("comp_config.json")
    with open(comp_config_path, 'w') as f:
        json.dump(dummy_comp_config_content, f, indent=2)

    print("\n--- Testing Compare Configs ---")
    # Base config is already loaded and modified ("MyUpdatedLoRA")
    # We need to reload the original base for a cleaner comparison against comp_config.json
    model.set_base_config(str(dummy_config_path)) # Reload original "TestLoRA_v1"
    print(f"Base config reloaded: {model.base_config.get('output_name')}, LR: {model.base_config.get('learning_rate')}")

    comparison_result = model.compare_loaded_configs(str(comp_config_path))
    print("Comparison Result:")
    print(comparison_result)

    print("\n--- Testing Filename Suggestion from Training Comment ---")
    model.working_config = { # Simulate a config with only training comment
        "training_comment": "mychar_concept by artist",
        "optimizer": "AdamW"
    }
    print(f"Suggested filename from comment: {model.suggest_filename()}") # Expected: mychar_concept_config.json

    model.working_config = {
        "output_name": "", # Empty output name
        "training_comment": "another concept",
        "optimizer": "AdamW"
    }
    print(f"Suggested filename from comment (output_name empty): {model.suggest_filename()}") # Expected: another_concept_config.json

    model.working_config = {
        "output_name": "Lora With Spaces",
        "training_comment": "",
    }
    print(f"Suggested filename with spaces: {model.suggest_filename()}") # Expected: Lora_With_Spaces_config.json

    model.working_config = {
        "output_name": "Invalid!@#Chars",
        "training_comment": "",
    }
    print(f"Suggested filename with invalid chars: {model.suggest_filename()}") # Expected: Invalid___Chars_config.json


    # Cleanup dummy files
    if dummy_config_path.exists():
        os.remove(dummy_config_path)
    if comp_config_path.exists():
        os.remove(comp_config_path)
    print("\n--- Tests Complete ---")

```

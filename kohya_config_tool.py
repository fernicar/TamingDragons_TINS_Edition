import gradio as gr
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re

class TamingDragons:
    def __init__(self):
        self.base_config = {}
        self.comparison_config = {}
        self.working_config = {}
        
        # Daily tweaks - the stuff that changes constantly
        self.daily_tweaks = {
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
        
        # Parameters that are important but less frequently changed
        self.important_params = {
            'optimizer': 'Optimizer',
            'lr_scheduler': 'LR Scheduler',
            'network_dim': 'Network Dimension',
            'network_alpha': 'Network Alpha',
            'noise_offset': 'Noise Offset',
            'min_snr_gamma': 'Min SNR Gamma',
            'save_every_n_epochs': 'Save Every N Epochs',
            'save_every_n_steps': 'Save Every N Steps'
        }

    def load_config(self, file_path: str) -> Tuple[Dict[str, Any], str]:
        """Load configuration file and return config + status message"""
        try:
            if not file_path or not os.path.exists(file_path):
                return {}, "No file selected"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Detect config type
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

    def load_base_config(self, file) -> Tuple[str, str, str, str, str, str, str, str, str, str]:
        """Load base configuration and populate daily tweaks"""
        if not file:
            return ("Select a base configuration file",) + ("",) * 9
        
        self.base_config, status = self.load_config(file.name)
        self.working_config = self.base_config.copy()
        
        if not self.base_config:
            return (status,) + ("",) * 9
        
        # Extract daily tweak values
        values = []
        for param in self.daily_tweaks.keys():
            value = self.working_config.get(param, "")
            values.append(str(value) if value is not None else "")
        
        return (status,) + tuple(values)

    def compare_configs(self, base_file, comp_file) -> str:
        """Compare base config with another config"""
        if not base_file or not comp_file:
            return "Please upload both configuration files"
        
        self.base_config, base_status = self.load_config(base_file.name)
        self.comparison_config, comp_status = self.load_config(comp_file.name)
        
        if not self.base_config or not self.comparison_config:
            return f"Error loading files:\n{base_status}\n{comp_status}"
        
        # Generate comparison
        comparison = []
        comparison.append("## 🔍 Configuration Comparison")
        comparison.append(f"**Base:** {base_status}")
        comparison.append(f"**Comparison:** {comp_status}")
        
        # Check daily tweaks differences
        daily_diffs = []
        for param, label in self.daily_tweaks.items():
            base_val = self.base_config.get(param, "Not set")
            comp_val = self.comparison_config.get(param, "Not set")
            
            if base_val != comp_val:
                daily_diffs.append(f"**{label}:**\n  Base: `{base_val}`\n  Comparison: `{comp_val}`")
        
        if daily_diffs:
            comparison.append("\n### 📝 Daily Tweaks Differences")
            comparison.extend(daily_diffs)
        
        # Check important parameter differences
        important_diffs = []
        for param, label in self.important_params.items():
            base_val = self.base_config.get(param, "Not set")
            comp_val = self.comparison_config.get(param, "Not set")
            
            if base_val != comp_val:
                important_diffs.append(f"**{label}:** `{base_val}` → `{comp_val}`")
        
        if important_diffs:
            comparison.append("\n### ⚙️ Important Parameter Differences")
            comparison.extend(important_diffs)
        
        # Check for exotic optimizer settings
        base_optimizer = self.base_config.get('optimizer', '')
        comp_optimizer = self.comparison_config.get('optimizer', '')
        
        if base_optimizer != comp_optimizer:
            comparison.append(f"\n### 🔧 Optimizer Change")
            comparison.append(f"**Base:** {base_optimizer}")
            comparison.append(f"**Comparison:** {comp_optimizer}")
            
            # Check for exotic args
            base_args = self.base_config.get('optimizer_args', '')
            comp_args = self.comparison_config.get('optimizer_args', '')
            
            if base_args != comp_args:
                comparison.append(f"\n**Optimizer Args Changed:**")
                comparison.append(f"Base: `{base_args}`")
                comparison.append(f"Comparison: `{comp_args}`")
        
        if not daily_diffs and not important_diffs and base_optimizer == comp_optimizer:
            comparison.append("\n✅ **Configurations are very similar!**")
        
        return "\n\n".join(comparison)

    def update_daily_tweaks(self, *values) -> str:
        """Update the working configuration with daily tweak values"""
        if not self.working_config:
            return "❌ Please load a base configuration first"
        
        param_keys = list(self.daily_tweaks.keys())
        
        for i, value in enumerate(values):
            if i < len(param_keys):
                param = param_keys[i]
                if value.strip():  # Only update if not empty
                    # Type conversion
                    original_val = self.working_config.get(param)
                    try:
                        if isinstance(original_val, int):
                            self.working_config[param] = int(value)
                        elif isinstance(original_val, float):
                            self.working_config[param] = float(value)
                        elif isinstance(original_val, bool):
                            self.working_config[param] = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            self.working_config[param] = value
                    except ValueError:
                        self.working_config[param] = value
        
        return "✅ Daily tweaks updated successfully!"

    def get_working_config_summary(self) -> str:
        """Get a summary of the current working configuration"""
        if not self.working_config:
            return "No configuration loaded"
        
        summary = []
        summary.append("## 🎯 Current Configuration Summary")
        
        # Show daily tweaks
        summary.append("### Daily Tweaks")
        for param, label in self.daily_tweaks.items():
            value = self.working_config.get(param, "Not set")
            summary.append(f"**{label}:** `{value}`")
        
        # Show key technical details
        summary.append("\n### Key Settings")
        for param, label in self.important_params.items():
            value = self.working_config.get(param, "Not set")
            summary.append(f"**{label}:** `{value}`")
        
        return "\n\n".join(summary)

    def save_config(self, filename: str) -> str:
        """Save the working configuration"""
        if not self.working_config:
            return "❌ No configuration to save"
        
        try:
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create directory if needed
            save_path = Path("configs") / filename
            save_path.parent.mkdir(exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.working_config, f, indent=2, ensure_ascii=False)
            
            return f"✅ Configuration saved as: {save_path}"
        
        except Exception as e:
            return f"❌ Error saving: {str(e)}"

    def generate_filename_suggestion(self, output_name: str, training_comment: str) -> str:
        """Generate a sensible filename from output name and training comment"""
        if not output_name and not training_comment:
            return ""
        
        # Use output_name if available, otherwise extract from training_comment
        if output_name:
            base = re.sub(r'[^\w\-_]', '_', output_name)
        else:
            # Extract trigger word from training_comment
            words = training_comment.split()[:2]  # First couple of words
            base = '_'.join(re.sub(r'[^\w]', '', word) for word in words if word)
        
        return f"{base}_config.json" if base else "modified_config.json"

def create_interface():
    tool = TamingDragons()
    
    with gr.Blocks(title="Taming Dragons - Kohya Config Tool", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🐉 Taming Dragons
        ### Kohya Configuration Management Tool
        
        **Easily modify your proven Stable Diffusion training configs without the hassle!**
        
        Perfect for changing output names, trigger words, sample prompts, and learning rates across multiple LoRA training runs.
        """)
        
        with gr.Tab("🎯 Quick Tweaks"):
            gr.Markdown("### Load Your Base Configuration")
            
            with gr.Row():
                base_file = gr.File(label="Upload Base Config", file_types=[".json"])
                load_status = gr.Textbox(label="Status", interactive=False, scale=2)
            
            gr.Markdown("### ⚡ Daily Tweaks - The Stuff You Change Every Time")
            
            with gr.Row():
                with gr.Column():
                    output_name = gr.Textbox(label="🎯 Output Name", placeholder="MyNewLoRA_v1")
                    training_comment = gr.Textbox(label="🏷️ Training Comment (Trigger Words)", placeholder="mynewlora woman, portrait")
                    sample_prompts = gr.Textbox(label="🖼️ Sample Prompts", lines=3, placeholder="mynewlora woman portrait, looking at viewer, detailed...")
                    learning_rate = gr.Textbox(label="📈 Learning Rate", placeholder="0.0001")
                    unet_lr = gr.Textbox(label="🧠 UNet Learning Rate", placeholder="0.0001")
                
                with gr.Column():
                    text_encoder_lr = gr.Textbox(label="📝 Text Encoder LR", placeholder="0.0001")
                    epoch = gr.Textbox(label="🔄 Epochs", placeholder="30")
                    max_train_steps = gr.Textbox(label="👟 Max Train Steps", placeholder="3000")
                    seed = gr.Textbox(label="🎲 Seed", placeholder="42")
                    train_batch_size = gr.Textbox(label="📦 Batch Size", placeholder="1")
            
            with gr.Row():
                update_btn = gr.Button("🔄 Update Configuration", variant="primary", scale=1)
                update_status = gr.Textbox(label="Update Status", interactive=False, scale=2)
            
            with gr.Accordion("📋 Current Configuration Summary", open=False):
                config_summary = gr.Markdown("Load a configuration to see summary")
        
        with gr.Tab("🔍 Compare Configs"):
            gr.Markdown("### Compare Two Configurations")
            gr.Markdown("Compare your base config with another to see what's different before tweaking.")
            
            with gr.Row():
                compare_base_file = gr.File(label="Base Configuration", file_types=[".json"])
                compare_comp_file = gr.File(label="Comparison Configuration", file_types=[".json"])
            
            compare_btn = gr.Button("🔍 Compare Configurations", variant="primary")
            comparison_result = gr.Markdown("Upload both files to compare")
        
        with gr.Tab("💾 Save Configuration"):
            gr.Markdown("### Save Your Modified Configuration")
            
            with gr.Row():
                with gr.Column():
                    suggested_filename = gr.Textbox(label="Suggested Filename", interactive=False)
                    save_filename = gr.Textbox(label="Save As", placeholder="my_new_config.json")
                    
                with gr.Column():
                    save_btn = gr.Button("💾 Save Configuration", variant="primary")
                    save_status = gr.Textbox(label="Save Status", interactive=False)
        
        # Event handlers
        base_file.change(
            tool.load_base_config,
            inputs=[base_file],
            outputs=[load_status, output_name, training_comment, sample_prompts, 
                    learning_rate, unet_lr, text_encoder_lr, epoch, max_train_steps, seed, train_batch_size]
        )
        
        update_btn.click(
            tool.update_daily_tweaks,
            inputs=[output_name, training_comment, sample_prompts, learning_rate, unet_lr, 
                   text_encoder_lr, epoch, max_train_steps, seed, train_batch_size],
            outputs=[update_status]
        ).then(
            tool.get_working_config_summary,
            outputs=[config_summary]
        )
        
        compare_btn.click(
            tool.compare_configs,
            inputs=[compare_base_file, compare_comp_file],
            outputs=[comparison_result]
        )
        
        # Auto-generate filename suggestion
        def update_filename_suggestion(out_name, comment):
            return tool.generate_filename_suggestion(out_name, comment)
        
        output_name.change(
            update_filename_suggestion,
            inputs=[output_name, training_comment],
            outputs=[suggested_filename]
        )
        
        training_comment.change(
            update_filename_suggestion,
            inputs=[output_name, training_comment],
            outputs=[suggested_filename]
        )
        
        save_btn.click(
            tool.save_config,
            inputs=[save_filename],
            outputs=[save_status]
        )
        
        # Auto-refresh summary when config is loaded
        base_file.change(
            tool.get_working_config_summary,
            outputs=[config_summary]
        )
    
    return interface

if __name__ == "__main__":
    # Create output directory
    os.makedirs("configs", exist_ok=True)
    
    # Launch interface
    interface = create_interface()
    interface.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True
    )

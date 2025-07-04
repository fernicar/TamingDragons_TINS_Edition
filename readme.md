# 🐉 Taming Dragons
### Kohya Configuration Management Tool

Welcome, weary LoRA trainers and configuration wranglers! Tired of diving into massive JSON files just to change "KezzieNv2" to "NewPersonV1" for the hundredth time? Fed up with hunting through endless parameters to tweak a learning rate or update sample prompts? **Frustrate no more!** 

Taming Dragons is here to be your trusty sidekick in the eternal quest of cranking out LoRA training configurations without losing your sanity. This delightful little Gradio app focuses on the stuff you *actually* change every day, whilst keeping all the exotic technical wizardry safely tucked away where it belongs.

✨ **Perfect companion to [How to Train Your Dragon](https://github.com/DragonDiffusionbyBoyo/HowToTrainYourDragon) and standard Kohya setups!**

## 🎯 What Does This Dragon Do?

Ever noticed how 90% of your config changes are the same few things?
- **Output name** (because "MyLoRA_v47_final_FINAL_actually_final" gets old)
- **Training comment** (trigger words that actually work)
- **Sample prompts** (testing your new subject without diving into JSON hell)
- **Learning rates** (the eternal tweaking dance)
- **Steps and epochs** (quick test vs. full training runs)

Meanwhile, all the exotic optimizer arguments, memory settings, and technical parameters stay exactly the same between training runs. **So why are we editing them every bloody time?**

Taming Dragons solves this by giving you a clean, focused interface for the daily grind parameters, whilst keeping the technical wizardry intact but out of your way.

## 🚀 Quick Start Spell-Casting

### 1. Conjure Your Virtual Environment 🧪
```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 2. Summon the Dependencies 📜
```bash
pip install gradio
```

That's it! No PyTorch shenanigans, no CUDA wrestling, just simple Python magic.

### 3. Unleash the Dragon! 🔥
```bash
python taming_dragons.py
```

The Gradio interface will launch in your browser at `http://127.0.0.1:7860`

## 🎮 How to Tame Your Dragon

### The Quick Tweaks Workflow (The Main Event)

1. **Load Your Base Config**: Upload your proven, working Kohya configuration
2. **Daily Tweaks Section**: The app automatically extracts and displays the parameters you actually change:
   - 🎯 Output Name
   - 🏷️ Training Comment (Trigger Words)  
   - 🖼️ Sample Prompts
   - 📈 Learning Rate
   - 🧠 UNet Learning Rate
   - 📝 Text Encoder Learning Rate
   - 🔄 Epochs
   - 👟 Max Train Steps
   - 🎲 Seed
   - 📦 Batch Size

3. **Make Your Changes**: Edit the fields that need updating
4. **Update Configuration**: One click to apply your changes
5. **Save**: The app suggests intelligent filenames based on your output name and trigger words

### Compare Configs (When You Need to See Differences)

Upload two configurations to see what's different between them. Perfect for:
- Comparing your base config with someone else's setup
- Seeing what changed between training runs
- Spotting exotic optimizer differences before making variants

### The Magic Behind the Scenes

**What stays the same**: All your exotic optimizer arguments (`decouple=True weight_decay=0.45 d_coef=2` and friends), model paths, memory settings, and technical parameters remain untouched.

**What gets easy**: The stuff you change every day becomes a simple form instead of JSON archaeology.

**Smart filename suggestions**: Based on your output name and trigger words, because `FluxLoRA_sarah_portrait_v3.json` is more useful than `config_copy_2_final.json`.

## 🧙‍♂️ Perfect For

- **LoRA trainers** who run multiple subjects with the same base setup
- **Kohya users** tired of JSON editing for simple parameter changes
- **Batch trainers** who need to quickly generate config variants
- **Anyone** who's ever spent 10 minutes hunting for the learning rate in a 200-line JSON file

## 🔧 Technical Sorcery

- **Flux1, SDXL, and Standard LoRA** configurations supported
- **Intelligent type conversion** (keeps your ints as ints, floats as floats)
- **Exotic optimizer detection** (flags when special Prodigy/AdamW8bit parameters exist)
- **Non-destructive editing** (your original config structure remains intact)
- **Auto-backup through versioning** (save variants without overwriting originals)

## 🤝 Dragon Diffusion Ecosystem

Taming Dragons is part of the Dragon Diffusion toolkit:
- **[How to Train Your Dragon](https://github.com/DragonDiffusionbyBoyo/HowToTrainYourDragon)**: Full training software based on Kohya
- **[Dragon Diffusion Dataset Validator](https://github.com/DragonDiffusionbyBoyo/Dragon-Diffusion-Dataset-Validator)**: Dataset analysis and quality checking
- **Taming Dragons**: Configuration management (you are here!)

## 🐛 When Dragons Misbehave

Found a bug? Configuration not loading properly? The dragon refusing to save your tweaks?

**Open an issue** and include:
- Your Python version
- The configuration file that's causing trouble (anonymise paths/names if needed)
- What you were trying to do when it broke

## 📜 The Ancient Wisdom (FAQ)

**Q: Will this work with my exotic Prodigy setup?**  
A: Absolutely! All the exotic parameters stay intact - we just make the common stuff easier to change.

**Q: Can I use this with non-Kohya configs?**  
A: It's designed for Kohya configs, but any JSON with similar parameter names should work fine.

**Q: What if I need to change something not in the daily tweaks?**  
A: The comparison tool shows all differences, and your saved config includes everything. You can always edit the saved JSON manually for the truly exotic stuff.

**Q: Does this replace Kohya GUI?**  
A: Not at all! This is for config management and quick tweaks. You still need Kohya or How to Train Your Dragon for the actual training.

---

*Built with ❤️ (and mild frustration at JSON editing) by Dragon Diffusion*

**May your training runs be swift and your configs ever-tidy!** 🐉✨
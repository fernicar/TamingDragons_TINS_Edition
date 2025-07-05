import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTabWidget, QGroupBox, QFormLayout, QLineEdit, QLabel,
    QFileDialog, QMessageBox, QMenuBar, QMenu, QStatusBar, QGridLayout,
    QStyleFactory, QComboBox
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Slot, Qt, QSettings

from model import TamingDragonsModel # Assuming model.py is in the same directory

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = TamingDragonsModel()
        self.current_base_config_path = None
        self.current_comp_config_path = None
        # For storing style/theme settings persistently
        self.settings = QSettings("TamingDragonsOrg", "KohyaConfigTool")
        self._init_ui()
        self._load_app_settings()


    def _init_ui(self):
        self.setWindowTitle("Taming Dragons - Kohya Config Tool")
        self.setGeometry(100, 100, 800, 700) # Adjusted default size

        # --- Menu Bar ---
        self._create_menu_bar()

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load a base configuration to start.")

        # --- Central Widget & Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Tab Widget ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Tab 1: Quick Tweaks ---
        self._create_quick_tweaks_tab()

        # --- Tab 2: Compare Configs ---
        self._create_compare_configs_tab()

        # --- Tab 3: Save Configuration ---
        self._create_save_config_tab()

        # Initial state for save tab (filename suggestion)
        self._update_suggested_filename_display()


    def _create_quick_tweaks_tab(self):
        quick_tweaks_tab = QWidget()
        layout = QVBoxLayout(quick_tweaks_tab)

        # Load Base Configuration Group
        load_group = QGroupBox("Load Base Configuration")
        load_layout = QHBoxLayout()
        load_button = QPushButton("Upload Base Config...")
        load_button.clicked.connect(self._load_base_config_dialog)
        load_layout.addWidget(load_button)
        self.load_status_label = QLabel("No config loaded.")
        self.load_status_label.setWordWrap(True)
        load_layout.addWidget(self.load_status_label, 1) # Give more space to label
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)

        # Daily Tweaks Group
        tweaks_group = QGroupBox("⚡ Daily Tweaks - The Stuff You Change Every Time")
        tweaks_form_layout = QFormLayout()

        self.tweak_inputs = {} # Store QLineEdit/QTextEdit widgets
        for key, label_text in self.model.daily_tweaks_map.items():
            # Use QTextEdit for sample_prompts, QLineEdit for others
            if key == 'sample_prompts':
                widget = QTextEdit()
                widget.setPlaceholderText(f"Enter {label_text.lower()} here...")
                widget.setFixedHeight(80) # Reasonable default height for prompts
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(f"Enter {label_text.lower()} here...")

            self.tweak_inputs[key] = widget
            tweaks_form_layout.addRow(f"{label_text}:", widget)

            # Connect textChanged for output_name and training_comment to update suggestion
            if key == 'output_name' or key == 'training_comment':
                widget.textChanged.connect(self._update_suggested_filename_display)

        tweaks_group.setLayout(tweaks_form_layout)
        layout.addWidget(tweaks_group)

        update_button = QPushButton("🔄 Update Configuration")
        update_button.clicked.connect(self._update_daily_tweaks_from_ui)
        layout.addWidget(update_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.update_status_label = QLabel("")
        layout.addWidget(self.update_status_label)

        # Configuration Summary Group (Collapsible/Expandable would be nice, simple for now)
        summary_group = QGroupBox("Current Configuration Summary")
        summary_layout = QVBoxLayout()
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.summary_display.setPlaceholderText("Load a configuration to see summary.")
        summary_layout.addWidget(self.summary_display)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        layout.addStretch(1) # Push content to top
        self.tabs.addTab(quick_tweaks_tab, "Quick Tweaks")

    def _create_compare_configs_tab(self):
        compare_tab = QWidget()
        layout = QVBoxLayout(compare_tab)

        layout.addWidget(QLabel("<h3>Compare Two Configurations</h3>"))
        layout.addWidget(QLabel("Compare your base config with another to see what's different."))

        # File Selection Group
        files_group = QGroupBox("Select Files for Comparison")
        files_layout = QGridLayout() # Use QGridLayout for better alignment

        base_btn = QPushButton("Select Base Configuration...")
        base_btn.clicked.connect(self._select_compare_base_file)
        files_layout.addWidget(base_btn, 0, 0)
        self.compare_base_file_label = QLabel("No base file selected.")
        self.compare_base_file_label.setWordWrap(True)
        files_layout.addWidget(self.compare_base_file_label, 0, 1)

        comp_btn = QPushButton("Select Comparison Configuration...")
        comp_btn.clicked.connect(self._select_compare_comp_file)
        files_layout.addWidget(comp_btn, 1, 0)
        self.compare_comp_file_label = QLabel("No comparison file selected.")
        self.compare_comp_file_label.setWordWrap(True)
        files_layout.addWidget(self.compare_comp_file_label, 1, 1)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        compare_run_button = QPushButton("🔍 Compare Configurations")
        compare_run_button.clicked.connect(self._run_comparison)
        layout.addWidget(compare_run_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.comparison_result_display = QTextEdit()
        self.comparison_result_display.setReadOnly(True)
        self.comparison_result_display.setPlaceholderText("Comparison results will appear here.")
        layout.addWidget(self.comparison_result_display)

        self.tabs.addTab(compare_tab, "Compare Configs")

    def _create_save_config_tab(self):
        save_tab = QWidget()
        layout = QVBoxLayout(save_tab)

        layout.addWidget(QLabel("<h3>Save Your Modified Configuration</h3>"))

        save_form_group = QGroupBox("Filename")
        save_form_layout = QFormLayout()

        self.suggested_filename_display = QLineEdit()
        self.suggested_filename_display.setReadOnly(True)
        save_form_layout.addRow("Suggested Filename:", self.suggested_filename_display)

        self.save_as_edit = QLineEdit()
        self.save_as_edit.setPlaceholderText("my_new_config.json or use suggestion")
        save_form_layout.addRow("Save As:", self.save_as_edit)
        save_form_group.setLayout(save_form_layout)
        layout.addWidget(save_form_group)

        save_run_button = QPushButton("💾 Save Configuration")
        save_run_button.clicked.connect(self._save_config_dialog) # Re-use dialog for consistency
        layout.addWidget(save_run_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.save_status_label = QLabel("")
        layout.addWidget(self.save_status_label)

        layout.addStretch(1)
        self.tabs.addTab(save_tab, "Save Configuration")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        load_action = QAction("Load &Base Config...", self)
        load_action.triggered.connect(self._load_base_config_dialog)
        file_menu.addAction(load_action)

        save_action = QAction("&Save Config As...", self)
        save_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_action.triggered.connect(self._save_config_dialog)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu for Styles and Color Schemes
        view_menu = menu_bar.addMenu("&View")

        # Style Submenu
        style_menu = view_menu.addMenu("&Style")
        self.style_actions = [] # Ensure this list is initialized here
        for style_name in QStyleFactory.keys():
            action = QAction(style_name, self)
            action.setCheckable(True)
            action.setData(style_name)
            action.triggered.connect(self._on_style_selected_menu)
            style_menu.addAction(action)
            self.style_actions.append(action)

        # Color Scheme Submenu
        color_scheme_menu = view_menu.addMenu("&Color Scheme")
        self.color_scheme_actions = [] # Ensure this list is initialized here

        # Define color schemes: Name, Qt.ColorScheme value
        schemes = [
            ("Auto", Qt.ColorScheme.Unknown),
            ("Light", Qt.ColorScheme.Light),
            ("Dark", Qt.ColorScheme.Dark)
        ]
        for name, scheme_val in schemes:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setData(scheme_val)
            action.triggered.connect(self._on_color_scheme_selected_menu)
            color_scheme_menu.addAction(action)
            self.color_scheme_actions.append(action)

    def _load_app_settings(self):
        """Loads and applies stored application settings like style and color scheme."""
        app = QApplication.instance()
        if not app: # Should not happen in a running app but good for robustness
            return

        # Load and apply style
        saved_style = self.settings.value("style", "Fusion") # Default to Fusion
        if saved_style in QStyleFactory.keys():
            # Pass the string name directly to setStyle
            app.setStyle(saved_style)
        else: # Fallback if saved style is somehow invalid
            app.setStyle("Fusion")
            saved_style = "Fusion" # Ensure settings reflect actual applied style
            self.settings.setValue("style", saved_style)

        for action in self.style_actions:
            action.setChecked(action.data() == saved_style)

        # Load and apply color scheme
        saved_scheme_val = self.settings.value("colorScheme", Qt.ColorScheme.Unknown.value, type=int)
        try:
            color_scheme_to_apply = Qt.ColorScheme(saved_scheme_val)
        except ValueError:
            color_scheme_to_apply = Qt.ColorScheme.Unknown # Fallback

        app.styleHints().setColorScheme(color_scheme_to_apply)
        for action in self.color_scheme_actions:
            action.setChecked(action.data() == color_scheme_to_apply)

    @Slot(bool)
    def _on_style_selected_menu(self, checked):
        action = self.sender()
        app = QApplication.instance()
        if not app or not isinstance(action, QAction) or not checked:
            return

        selected_style_name = action.data()
        # Pass the string name directly
        app.setStyle(selected_style_name)
        self.settings.setValue("style", selected_style_name)

        # Uncheck other style actions
        for style_action in self.style_actions:
            if style_action != action:
                style_action.setChecked(False)
        action.setChecked(True) # Ensure the clicked one remains checked
        self.status_bar.showMessage(f"Style set to {selected_style_name}", 3000)


    @Slot(bool)
    def _on_color_scheme_selected_menu(self, checked):
        action = self.sender()
        app = QApplication.instance()
        if not app or not isinstance(action, QAction) or not checked:
            return

        selected_scheme_val = action.data() # This is Qt.ColorScheme enum member
        app.styleHints().setColorScheme(selected_scheme_val)
        self.settings.setValue("colorScheme", selected_scheme_val.value) # Store the integer value

        # Uncheck other color scheme actions
        for scheme_action in self.color_scheme_actions:
            if scheme_action != action:
                scheme_action.setChecked(False)
        action.setChecked(True)
        self.status_bar.showMessage(f"Color scheme set to {action.text()}", 3000)


    @Slot()
    def _load_base_config_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Base Configuration", "", "JSON files (*.json)")
        if file_path:
            self.current_base_config_path = file_path # Store for comparison use
            status, tweak_values = self.model.set_base_config(file_path)
            self.load_status_label.setText(status)
            self.status_bar.showMessage(status, 5000)
            if tweak_values:
                for key, value_str in tweak_values.items():
                    if key in self.tweak_inputs:
                        if isinstance(self.tweak_inputs[key], QTextEdit):
                             self.tweak_inputs[key].setPlainText(value_str)
                        else: # QLineEdit
                             self.tweak_inputs[key].setText(value_str)
                self._update_config_summary_display()
                self._update_suggested_filename_display() # Update suggestion in Save tab
                QMessageBox.information(self, "Config Loaded", status)
            else:
                QMessageBox.warning(self, "Load Error", status)

    @Slot()
    def _update_daily_tweaks_from_ui(self):
        if not self.model.working_config:
            QMessageBox.warning(self, "Error", "Please load a base configuration first.")
            self.update_status_label.setText("❌ Please load a base configuration first")
            return

        new_values = {}
        for key, widget in self.tweak_inputs.items():
            if isinstance(widget, QTextEdit):
                new_values[key] = widget.toPlainText()
            else: # QLineEdit
                new_values[key] = widget.text()

        status = self.model.update_working_config_daily_tweaks(new_values)
        self.update_status_label.setText(status)
        self.status_bar.showMessage(status, 3000)
        self._update_config_summary_display()
        self._update_suggested_filename_display() # Filename might change

    def _update_config_summary_display(self):
        summary_md = self.model.get_working_config_summary_markdown()
        self.summary_display.setMarkdown(summary_md)

    @Slot()
    def _select_compare_base_file(self):
        # If a base config is already loaded via Quick Tweaks, use that.
        if self.current_base_config_path:
            self.compare_base_file_label.setText(f"Using current base: {Path(self.current_base_config_path).name}")
            # No need to select again, but we could offer to change it.
            # For now, this implies the "Compare Configs" tab uses the globally loaded base config.
            # If we want it independent, this button should always open a dialog.
            # Let's make it independent for clarity in this tab:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Base File for Comparison", "", "JSON files (*.json)")
            if file_path:
                self.current_base_config_path_for_compare = file_path # Store separately for compare tab
                self.compare_base_file_label.setText(Path(file_path).name)
            return

        # Fallback if no global base config path is set
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base File for Comparison", "", "JSON files (*.json)")
        if file_path:
            self.current_base_config_path_for_compare = file_path
            self.compare_base_file_label.setText(Path(file_path).name)


    @Slot()
    def _select_compare_comp_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Comparison File", "", "JSON files (*.json)")
        if file_path:
            self.current_comp_config_path = file_path
            self.compare_comp_file_label.setText(Path(file_path).name)

    @Slot()
    def _run_comparison(self):
        base_to_compare = getattr(self, 'current_base_config_path_for_compare', self.current_base_config_path)

        if not base_to_compare:
            QMessageBox.warning(self, "Error", "Please select a Base Configuration file for comparison.")
            return
        if not self.current_comp_config_path:
            QMessageBox.warning(self, "Error", "Please select a Comparison Configuration file.")
            return

        # Temporarily load the selected base file for comparison if it's different from the globally loaded one
        # This is a bit complex. Simpler: always use the globally loaded base_config from the model.
        # The user should load their primary "base" in the Quick Tweaks tab first.
        if not self.model.base_config:
             QMessageBox.warning(self, "Error", "Please load a primary Base Configuration in the 'Quick Tweaks' tab first.")
             return

        # Perform comparison using the model's current base_config against current_comp_config_path
        result_md = self.model.compare_loaded_configs(self.current_comp_config_path)
        self.comparison_result_display.setMarkdown(result_md)
        self.status_bar.showMessage("Comparison complete.", 3000)

    @Slot()
    def _update_suggested_filename_display(self):
        if self.model.working_config: # Only suggest if a config is loaded
            suggestion = self.model.suggest_filename()
            self.suggested_filename_display.setText(suggestion)
            if not self.save_as_edit.text(): # If user hasn't typed anything, prefill
                self.save_as_edit.setText(suggestion)
        else:
            self.suggested_filename_display.setText("Load a config first")
            self.save_as_edit.setText("")


    @Slot()
    def _save_config_dialog(self):
        if not self.model.working_config:
            QMessageBox.warning(self, "Error", "No configuration loaded to save.")
            self.save_status_label.setText("❌ No configuration loaded to save.")
            return

        suggested_filename = self.model.suggest_filename()
        user_specified_filename = self.save_as_edit.text().strip()

        final_filename_to_use = user_specified_filename if user_specified_filename else suggested_filename

        # The QFileDialog is more for choosing a *path* and name,
        # but our model handles the `configs/` subdir.
        # So we can directly use the model's save.
        # If we wanted a full dialog for choosing location:
        # save_dir = Path("configs")
        # save_dir.mkdir(parents=True, exist_ok=True)
        # default_save_path = str(save_dir / final_filename_to_use)
        # file_path, _ = QFileDialog.getSaveFileName(self, "Save Configuration As", default_save_path, "JSON files (*.json)")
        # if file_path:
        #    # Need to ensure the model saves to this exact file_path, potentially bypassing its own `configs/` logic
        #    # For simplicity, let's stick to saving in `configs/` based on filename input.
        #    filename_only = Path(file_path).name
        #    status = self.model.save_working_config(filename_only)
        # else: ...

        if not final_filename_to_use:
            QMessageBox.warning(self, "Error", "Filename cannot be empty.")
            self.save_status_label.setText("❌ Filename cannot be empty.")
            return

        status = self.model.save_working_config(final_filename_to_use)
        self.save_status_label.setText(status)
        self.status_bar.showMessage(status, 5000)
        if "✅" in status:
            QMessageBox.information(self, "Config Saved", status)
        else:
            QMessageBox.warning(self, "Save Error", status)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set default style to Fusion and color scheme to Auto (Unknown) before MainWindow loads settings
    # This ensures a known baseline if settings are corrupted or not yet saved.
    # MainWindow._load_app_settings() will then override with saved preferences if available.
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    app.styleHints().setColorScheme(Qt.ColorScheme.Unknown) # Auto

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Removed triple backticks that caused SyntaxError

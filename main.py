import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTabWidget, QGroupBox, QFormLayout, QLineEdit, QLabel,
    QFileDialog, QMessageBox, QMenuBar, QMenu, QStatusBar, QGridLayout,
    QStyleFactory, QSplitter # Added QSplitter
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Slot, Qt, QSettings

from model import TamingDragonsModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = TamingDragonsModel()
        self.current_base_config_path = None
        self.current_comp_config_path = None
        self.settings = QSettings("TamingDragonsOrg", "KohyaConfigTool")
        self._init_ui()
        self._load_app_settings()

    def _init_ui(self):
        self.setWindowTitle("Taming Dragons - Kohya Config Tool")
        self.setGeometry(100, 100, 900, 700) # Increased width for splitter

        self._create_menu_bar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load a base configuration to start.")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._create_quick_tweaks_tab()
        self._create_compare_configs_tab()
        self._create_save_config_tab()

        self._update_suggested_filename_display()

    def _create_quick_tweaks_tab(self):
        quick_tweaks_tab = QWidget()
        tab_main_layout = QHBoxLayout(quick_tweaks_tab) # Main layout for this tab

        # --- Left Panel (Inputs) ---
        left_panel_widget = QWidget()
        left_layout = QVBoxLayout(left_panel_widget)

        load_group = QGroupBox("Load Base Configuration")
        load_layout = QHBoxLayout()
        load_button = QPushButton("Upload Base Config...")
        load_button.clicked.connect(self._load_base_config_dialog)
        load_layout.addWidget(load_button)
        self.load_status_label = QLabel("No config loaded.")
        self.load_status_label.setWordWrap(True)
        load_layout.addWidget(self.load_status_label, 1)
        load_group.setLayout(load_layout)
        left_layout.addWidget(load_group)

        tweaks_group = QGroupBox("⚡ Daily Tweaks - The Stuff You Change Every Time")
        tweaks_form_layout = QFormLayout()
        self.tweak_inputs = {}
        for key, label_text in self.model.daily_tweaks_map.items():
            if key == 'sample_prompts':
                widget = QTextEdit()
                widget.setPlaceholderText(f"Enter {label_text.lower()} here...")
                widget.setFixedHeight(80)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(f"Enter {label_text.lower()} here...")
            self.tweak_inputs[key] = widget
            tweaks_form_layout.addRow(f"{label_text}:", widget)
            if key == 'output_name' or key == 'training_comment':
                widget.textChanged.connect(self._update_suggested_filename_display)
        tweaks_group.setLayout(tweaks_form_layout)
        left_layout.addWidget(tweaks_group)

        update_button = QPushButton("🔄 Update Configuration")
        update_button.clicked.connect(self._update_daily_tweaks_from_ui)
        left_layout.addWidget(update_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.update_status_label = QLabel("")
        left_layout.addWidget(self.update_status_label)
        left_layout.addStretch(1)

        # --- Right Panel (Summary) ---
        summary_group = QGroupBox("Current Configuration Summary")
        summary_layout = QVBoxLayout()
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.summary_display.setPlaceholderText("Load a configuration to see summary.")
        summary_layout.addWidget(self.summary_display)
        summary_group.setLayout(summary_layout)

        # --- Splitter ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel_widget)
        splitter.addWidget(summary_group)
        # Initial sizing: give 60% to left, 40% to right, but they are resizable
        splitter.setSizes([self.width() * 0.6, self.width() * 0.4])

        tab_main_layout.addWidget(splitter)
        self.tabs.addTab(quick_tweaks_tab, "Quick Tweaks")


    def _create_compare_configs_tab(self):
        compare_tab = QWidget()
        layout = QVBoxLayout(compare_tab)
        layout.addWidget(QLabel("<h3>Compare Two Configurations</h3>"))
        layout.addWidget(QLabel("Compare your base config with another to see what's different."))
        files_group = QGroupBox("Select Files for Comparison")
        files_layout = QGridLayout()
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
        save_run_button.clicked.connect(self._save_config_dialog)
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
        view_menu = menu_bar.addMenu("&View")
        style_menu = view_menu.addMenu("&Style")
        self.style_actions = []
        for style_name in QStyleFactory.keys():
            action = QAction(style_name, self)
            action.setCheckable(True)
            action.setData(style_name)
            action.triggered.connect(self._on_style_selected_menu)
            style_menu.addAction(action)
            self.style_actions.append(action)
        color_scheme_menu = view_menu.addMenu("&Color Scheme")
        self.color_scheme_actions = []
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
        app = QApplication.instance()
        if not app: return

        saved_style = self.settings.value("style", "Fusion")
        if isinstance(saved_style, str) and saved_style in QStyleFactory.keys():
            app.setStyle(saved_style)
        else:
            app.setStyle("Fusion")
            saved_style = "Fusion"
            self.settings.setValue("style", saved_style)

        for action in self.style_actions: # self.style_actions might not be init yet if called too early
             if hasattr(self, 'style_actions'):
                action.setChecked(action.data() == saved_style)

        saved_scheme_val = self.settings.value("colorScheme", Qt.ColorScheme.Unknown.value, type=int)
        try:
            color_scheme_to_apply = Qt.ColorScheme(saved_scheme_val)
        except ValueError:
            color_scheme_to_apply = Qt.ColorScheme.Unknown

        app.styleHints().setColorScheme(color_scheme_to_apply)
        if hasattr(self, 'color_scheme_actions'):
            for action in self.color_scheme_actions:
                action.setChecked(action.data() == color_scheme_to_apply)

    @Slot(bool)
    def _on_style_selected_menu(self, checked):
        action = self.sender()
        app = QApplication.instance()
        if not app or not isinstance(action, QAction) or not checked: return

        selected_style_name = action.data()
        if isinstance(selected_style_name, str): # Ensure it's a string
            app.setStyle(selected_style_name)
            self.settings.setValue("style", selected_style_name)
            for style_action in self.style_actions:
                if style_action != action: style_action.setChecked(False)
            action.setChecked(True)
            self.status_bar.showMessage(f"Style set to {selected_style_name}", 3000)

    @Slot(bool)
    def _on_color_scheme_selected_menu(self, checked):
        action = self.sender()
        app = QApplication.instance()
        if not app or not isinstance(action, QAction) or not checked: return

        selected_scheme_val = action.data()
        if isinstance(selected_scheme_val, Qt.ColorScheme): # Ensure it's correct type
            app.styleHints().setColorScheme(selected_scheme_val)
            self.settings.setValue("colorScheme", selected_scheme_val.value)
            for scheme_action in self.color_scheme_actions:
                if scheme_action != action: scheme_action.setChecked(False)
            action.setChecked(True)
            self.status_bar.showMessage(f"Color scheme set to {action.text()}", 3000)

    @Slot()
    def _load_base_config_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Base Configuration", "", "JSON files (*.json)")
        if file_path:
            self.current_base_config_path = file_path
            status, tweak_values = self.model.set_base_config(file_path)
            self.load_status_label.setText(status)
            self.status_bar.showMessage(status, 5000)
            if tweak_values:
                for key, value_str in tweak_values.items():
                    if key in self.tweak_inputs:
                        if isinstance(self.tweak_inputs[key], QTextEdit):
                             self.tweak_inputs[key].setPlainText(value_str)
                        else:
                             self.tweak_inputs[key].setText(value_str)
                self._update_config_summary_display()
                self._update_suggested_filename_display()
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
            else:
                new_values[key] = widget.text()
        status = self.model.update_working_config_daily_tweaks(new_values)
        self.update_status_label.setText(status)
        self.status_bar.showMessage(status, 3000)
        self._update_config_summary_display()
        self._update_suggested_filename_display()

    def _update_config_summary_display(self):
        summary_md = self.model.get_working_config_summary_markdown()
        self.summary_display.setMarkdown(summary_md)

    @Slot()
    def _select_compare_base_file(self):
        if self.current_base_config_path:
            self.compare_base_file_label.setText(f"Using current base: {Path(self.current_base_config_path).name}")
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Base File for Comparison", "", "JSON files (*.json)")
            if file_path:
                self.current_base_config_path_for_compare = file_path
                self.compare_base_file_label.setText(Path(file_path).name)
            return
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
        if not self.model.base_config:
             QMessageBox.warning(self, "Error", "Please load a primary Base Configuration in the 'Quick Tweaks' tab first.")
             return
        result_md = self.model.compare_loaded_configs(self.current_comp_config_path)
        self.comparison_result_display.setMarkdown(result_md)
        self.status_bar.showMessage("Comparison complete.", 3000)

    @Slot()
    def _update_suggested_filename_display(self):
        if self.model.working_config:
            suggestion = self.model.suggest_filename()
            self.suggested_filename_display.setText(suggestion)
            if not self.save_as_edit.text():
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
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

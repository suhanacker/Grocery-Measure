import ttkbootstrap as ttk # type: ignore
from ttkbootstrap.constants import * # type: ignore
import json
import os
from typing import List, Dict
import csv
from tkinter import filedialog
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter  # Add this import at the top
import pyscreenshot as ImageGrab

class DataManager:
    def __init__(self):
        self.data_file = "light_measure_data.json"
        self.default_data = {
            "history": [],
            "default_price": "",
            "preferred_unit": "g",  # Default unit
            "base_unit": "kg"  # Default base unit
        }
        
    def save_data(self, history, default_price, preferred_unit, base_unit):
        data = {
            "history": history,
            "default_price": default_price,
            "preferred_unit": preferred_unit,
            "base_unit": base_unit
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f)
            
    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return self.default_data
        except:
            return self.default_data

class LightMeasureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Measure")
        self.root.geometry("500x900")
        
        # Set theme and colors
        self.style = ttk.Style("darkly")
        self.primary_color = "primary"
        
        # Price per kg variable
        self.price_per_kg = ttk.StringVar(value='')
        
        # Add history storage
        self.calculation_history = []
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Load saved data
        saved_data = self.data_manager.load_data()
        
        # Variables
        self.price_per_kg = ttk.StringVar(value=saved_data["default_price"])
        self.preferred_unit = ttk.StringVar(value=saved_data["preferred_unit"])
        self.calculation_history = saved_data["history"]
        
        # Add base unit variable
        self.base_unit = ttk.StringVar(value=saved_data.get("base_unit", "kg"))
        
        # Update unit factors with display names
        self.unit_info: Dict[str, Dict] = {
            "g": {"factor": 1, "display": "Gram (g)"},
            "kg": {"factor": 1000, "display": "Kilogram (kg)"},
            "lb": {"factor": 453.592, "display": "Pound (lb)"},
            "oz": {"factor": 28.3495, "display": "Ounce (oz)"}
        }
        
        # Add new variable for bulk results
        self.bulk_results: List[dict] = []
        
        # Create styles for overlay and popup
        style = ttk.Style()
        style.configure('dark.TFrame', background='#00000040')  # Semi-transparent black
        style.configure('light.TFrame', background='white', borderwidth=1, relief='solid')
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_container = ttk.Frame(self.root, padding=20)
        main_container.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text="Light Measure",
            font=('Roboto', 24, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Price Input Frame
        price_frame = ttk.LabelFrame(
            main_container,
            text="Price Input",
            padding=15,
            bootstyle="primary"
        )
        price_frame.pack(fill='x', pady=10)
        
        # Price input container (for horizontal layout)
        price_container = ttk.Frame(price_frame)
        price_container.pack(fill='x', pady=(0, 5))
        
        # Dynamic price label that updates with base unit
        self.price_label = ttk.Label(
            price_container,
            text="Price per",
            font=('Roboto', 12)
        )
        self.price_label.pack(side='left', padx=(0, 10))
        
        # Price entry (expanded)
        self.price_entry = ttk.Entry(
            price_container,
            textvariable=self.price_per_kg,
            font=('Roboto', 12)
        )
        self.price_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Base unit combobox (fixed width)
        self.base_unit_combo = ttk.Combobox(
            price_container,
            textvariable=self.base_unit,
            values=[info["display"] for info in self.unit_info.values()],
            state="readonly",
            font=('Roboto', 12),
            width=15
        )
        self.base_unit_combo.pack(side='left')
        self.base_unit_combo.bind('<<ComboboxSelected>>', self.update_price_label)
        
        # Create unit selection frame
        self.create_unit_selection_frame(main_container)
        
        # Create notebook
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=False, pady=10)
        
        # Create tabs
        self.create_weight_to_price_tab()
        self.create_price_to_weight_tab()
        self.create_bulk_calc_tab()
        
        # Create history frame
        self.create_history_frame(main_container)
        
        # Set a minimum window size
        self.root.minsize(500, 600)  # Adjust these values as needed

    def add_clear_button(self, parent_frame, widgets_to_clear):
        """Add a clear button that clears specified widgets"""
        def clear_fields():
            for widget in widgets_to_clear:
                if isinstance(widget, ttk.Entry):
                    widget.delete(0, 'end')
                elif isinstance(widget, ttk.Label):
                    if 'Price' in widget.cget('text'):
                        widget.config(text="Price: ₹0.00")
                    elif 'Weight' in widget.cget('text'):
                        widget.config(text="Weight: 0.00")
        
        ttk.Button(
            parent_frame,
            text="Clear",
            command=clear_fields,
            bootstyle="danger-outline",
            padding=10
        ).pack(side='left', expand=True, padx=5)

    def clear_fields(self, fields):
        for field in fields:
            if isinstance(field, ttk.Entry):
                field.delete(0, 'end')
            elif isinstance(field, ttk.Label):
                field.config(text="")

    def clear_history(self):
        self.calculation_history.clear()
        self.history_text.delete(1.0, 'end')
        self.save_data()

    def validate_number(self, value):
        try:
            num = float(value)
            return num >= 0
        except ValueError:
            return False

    def create_calculator_frame(self, parent):
        frame = ttk.Frame(parent, padding=15)
        
        # Create notebook for different calculation modes
        calc_notebook = ttk.Notebook(frame)
        calc_notebook.pack(fill='both', expand=True)
        
        # Weight to Price tab
        weight_price_frame = ttk.Frame(calc_notebook, padding=10)
        calc_notebook.add(weight_price_frame, text="Weight → Price")
        
        # Weight input with unit selection
        weight_container = ttk.Frame(weight_price_frame)
        weight_container.pack(fill='x', pady=5)
        
        weight_label = ttk.Label(
            weight_container,
            text="Weight:",
            font=('Roboto', 12)
        )
        weight_label.pack(side='left', padx=(0, 10))
        
        self.weight_entry = ttk.Entry(
            weight_container,
            font=('Roboto', 12)
        )
        self.weight_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Unit selection for weight input
        self.weight_unit_combo = ttk.Combobox(
            weight_container,
            textvariable=self.preferred_unit,
            values=[info["display"] for info in self.unit_info.values()],
            state="readonly",
            font=('Roboto', 12),
            width=15
        )
        self.weight_unit_combo.pack(side='left')
        
        calculate_price_btn = ttk.Button(
            weight_price_frame,
            text="Calculate Price",
            command=self.calculate_price,
            bootstyle="primary",
            padding=10
        )
        calculate_price_btn.pack(fill='x', pady=10)
        
        self.price_result = ttk.Label(
            weight_price_frame,
            text="Total Price: ₹0.00",
            font=('Roboto', 14)
        )
        self.price_result.pack(pady=10)
        
        # Price to Weight tab
        price_weight_frame = ttk.Frame(calc_notebook, padding=10)
        calc_notebook.add(price_weight_frame, text="Price → Weight")
        
        # Price input
        price_calc_container = ttk.Frame(price_weight_frame)
        price_calc_container.pack(fill='x', pady=5)
        
        price_calc_label = ttk.Label(
            price_calc_container,
            text="Price (₹):",
            font=('Roboto', 12)
        )
        price_calc_label.pack(side='left', padx=(0, 10))
        
        self.price_calc_entry = ttk.Entry(
            price_calc_container,
            font=('Roboto', 12)
        )
        self.price_calc_entry.pack(side='left', fill='x', expand=True)
        
        # Result unit selection frame
        result_unit_frame = ttk.Frame(price_weight_frame)
        result_unit_frame.pack(fill='x', pady=5)
        
        result_unit_label = ttk.Label(
            result_unit_frame,
            text="Result Unit:",
            font=('Roboto', 12)
        )
        result_unit_label.pack(side='left', padx=(0, 10))
        
        # Unit selection for weight result
        self.result_unit_combo = ttk.Combobox(
            result_unit_frame,
            textvariable=self.preferred_unit,
            values=[info["display"] for info in self.unit_info.values()],
            state="readonly",
            font=('Roboto', 12),
            width=15
        )
        self.result_unit_combo.pack(side='left')
        
        calculate_weight_btn = ttk.Button(
            price_weight_frame,
            text="Calculate Weight",
            command=self.calculate_weight,
            bootstyle="primary",
            padding=10
        )
        calculate_weight_btn.pack(fill='x', pady=10)
        
        self.weight_result = ttk.Label(
            price_weight_frame,
            text="Weight: 0.00",
            font=('Roboto', 14)
        )
        self.weight_result.pack(pady=10)
        
        # Bulk Calculations tab
        bulk_frame = ttk.Frame(calc_notebook, padding=10)
        calc_notebook.add(bulk_frame, text="Bulk Calc")
        
        # Bulk input unit selection
        bulk_unit_frame = ttk.Frame(bulk_frame)
        bulk_unit_frame.pack(fill='x', pady=5)
        
        bulk_unit_label = ttk.Label(
            bulk_unit_frame,
            text="Input Unit:",
            font=('Roboto', 12)
        )
        bulk_unit_label.pack(side='left', padx=(0, 10))
        
        # Unit selection for bulk calculations
        self.bulk_unit_combo = ttk.Combobox(
            bulk_unit_frame,
            textvariable=self.preferred_unit,
            values=[info["display"] for info in self.unit_info.values()],
            state="readonly",
            font=('Roboto', 12),
            width=15
        )
        self.bulk_unit_combo.pack(side='left')
        
        # Bulk input text area
        bulk_input_label = ttk.Label(
            bulk_frame,
            text="Enter values (one per line):",
            font=('Roboto', 12)
        )
        bulk_input_label.pack(anchor='w', pady=(10, 5))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(bulk_frame)
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.bulk_input = ttk.Text(
            text_frame,
            height=3,
            font=('Roboto', 12),
            yscrollcommand=scrollbar.set,
            wrap='none'
        )
        self.bulk_input.pack(fill='both', expand=True)
        scrollbar.config(command=self.bulk_input.yview)
        self.bulk_input.bind('<KeyRelease>', self.update_text_height)
        
        # Bulk calculation buttons
        button_frame = ttk.Frame(bulk_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            button_frame,
            text="Calculate Bulk",
            command=self.calculate_bulk,
            bootstyle="primary",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        ttk.Button(
            button_frame,
            text="Export CSV",
            command=self.export_bulk_results,
            bootstyle="success",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: self.bulk_input.delete(1.0, 'end'),
            bootstyle="danger-outline",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        # Bulk results display
        self.bulk_result_text = ttk.Text(
            bulk_frame,
            height=8,
            font=('Roboto', 12)
        )
        self.bulk_result_text.pack(fill='both', expand=True, pady=10)
        
        return frame

    def convert_to_grams(self, value, from_unit):
        return value * self.unit_info[from_unit]["factor"]
        
    def convert_from_grams(self, grams, to_unit):
        return grams / self.unit_info[to_unit]["factor"]

    def get_price_label(self) -> str:
        """Generate the price label based on selected base unit"""
        selected_display = self.base_unit_combo.get() if hasattr(self, 'base_unit_combo') else self.unit_info["kg"]["display"]
        return f"Price per {selected_display}"

    def update_price_label(self, event=None):
        """Update the price label when base unit changes"""
        # Price label now only shows "Price per" as the unit is shown in combobox
        pass

    def get_base_unit_code(self) -> str:
        """Get the unit code from the display name"""
        selected_display = self.base_unit_combo.get()
        for code, info in self.unit_info.items():
            if info["display"] == selected_display:
                return code
        return "kg"  # default fallback

    def calculate_price(self):
        try:
            if not self.price_per_kg.get():
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter base price first"
                )
                return
                
            weight = self.weight_entry.get()
            if not self.validate_number(weight):
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter a valid positive number"
                )
                return
                
            weight = float(weight)
            # Convert input weight to base unit
            base_unit_code = self.get_base_unit_code()
            weight_in_base = self.convert_between_units(
                weight,
                from_unit=self.preferred_unit.get(),
                to_unit=base_unit_code
            )
            price = weight_in_base * float(self.price_per_kg.get())
            result_text = f"Total Price: ₹{price:.2f}"
            
            self.price_result.config(
                text=result_text,
                bootstyle="primary"
            )
            
            # Add to history with unit
            history_entry = f"Weight: {weight}{self.preferred_unit.get()} → {result_text}\n"
            self.calculation_history.append(history_entry)
            self.update_history()
            self.save_data()
            
        except ValueError:
            ttk.Messagebox.show_error(
                title="Error",
                message="Please enter valid numbers"
            )

    def calculate_weight(self):
        try:
            if not self.price_per_kg.get():
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter base price first"
                )
                return
                
            price = self.price_calc_entry.get()
            if not self.validate_number(price):
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter a valid positive number"
                )
                return
                
            price = float(price)
            base_unit_code = self.get_base_unit_code()
            # Calculate weight in base unit
            weight_in_base = price / float(self.price_per_kg.get())
            # Convert to preferred unit
            weight = self.convert_between_units(
                weight_in_base,
                from_unit=base_unit_code,
                to_unit=self.preferred_unit.get()
            )
            result_text = f"Weight: {weight:.2f} {self.preferred_unit.get()}"
            
            self.weight_result.config(
                text=result_text,
                bootstyle="primary"
            )
            
            # Add to history
            history_entry = f"Price: ₹{price} → {result_text}\n"
            self.calculation_history.append(history_entry)
            self.update_history()
            self.save_data()
            
        except ValueError:
            ttk.Messagebox.show_error(
                title="Error",
                message="Please enter valid numbers"
            )

    def convert_between_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between any two units"""
        # Convert to grams first
        grams = value * self.unit_info[from_unit]["factor"]
        # Then convert to target unit
        return grams / self.unit_info[to_unit]["factor"]

    def save_data(self):
        self.data_manager.save_data(
            self.calculation_history,
            self.price_per_kg.get(),
            self.preferred_unit.get(),
            self.base_unit.get()  # Add base unit to saved data
        )

    def update_history(self):
        self.history_text.delete(1.0, 'end')
        for entry in self.calculation_history:
            self.history_text.insert('end', entry)

    def create_bulk_calc_widgets(self, parent):
        """Create widgets for bulk calculations tab"""
        # Text area for input
        input_frame = ttk.LabelFrame(
            parent,
            text="Bulk Input (One value per line)",
            padding=15,
            bootstyle="primary"
        )
        input_frame.pack(fill='x', pady=10)
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(fill='both', expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.bulk_input = ttk.Text(
            text_frame,
            height=3,
            font=('Roboto', 12),
            yscrollcommand=scrollbar.set,
            wrap='none'
        )
        self.bulk_input.pack(fill='both', expand=True)
        scrollbar.config(command=self.bulk_input.yview)
        self.bulk_input.bind('<KeyRelease>', self.update_text_height)
        
        # Mode and unit selection container
        mode_unit_frame = ttk.Frame(parent)
        mode_unit_frame.pack(fill='x', pady=10)
        
        # Mode selection
        mode_frame = ttk.LabelFrame(
            mode_unit_frame,
            text="Calculation Mode",
            padding=10,
            bootstyle="primary"
        )
        mode_frame.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.bulk_mode = ttk.StringVar(value="weight_to_price")
        ttk.Radiobutton(
            mode_frame,
            text="Weight → Price",
            variable=self.bulk_mode,
            value="weight_to_price",
            bootstyle="primary-toolbutton"
        ).pack(side='left', expand=True)
        
        ttk.Radiobutton(
            mode_frame,
            text="Price → Weight",
            variable=self.bulk_mode,
            value="price_to_weight",
            bootstyle="primary-toolbutton"
        ).pack(side='left', expand=True)
        
        # Unit selection for bulk calculations
        unit_frame = ttk.LabelFrame(
            mode_unit_frame,
            text="Unit Selection",
            padding=10,
            bootstyle="primary"
        )
        unit_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        self.bulk_unit_combo = ttk.Combobox(
            unit_frame,
            textvariable=self.preferred_unit,
            values=[info["display"] for info in self.unit_info.values()],
            state="readonly",
            font=('Roboto', 12)
        )
        self.bulk_unit_combo.pack(fill='x')
        
        # Buttons frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            button_frame,
            text="Calculate Bulk",
            command=self.calculate_bulk,
            bootstyle="primary",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        ttk.Button(
            button_frame,
            text="Export CSV",
            command=self.export_bulk_results,
            bootstyle="success",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: self.bulk_input.delete(1.0, 'end'),
            bootstyle="danger-outline",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        # Results display
        self.bulk_result_text = ttk.Text(
            parent,
            height=8,
            font=('Roboto', 12)
        )
        self.bulk_result_text.pack(fill='both', expand=True, pady=10)

    def calculate_bulk(self):
        """Process bulk calculations"""
        try:
            if not self.price_per_kg.get():
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter price per kg first"
                )
                return
            
            # Clear previous results
            self.bulk_results.clear()
            self.bulk_result_text.delete(1.0, 'end')
            
            # Get input values
            input_text = self.bulk_input.get(1.0, 'end').strip()
            values = [line.strip() for line in input_text.split('\n') if line.strip()]
            
            for value in values:
                if not self.validate_number(value):
                    ttk.Messagebox.show_error(
                        title="Error",
                        message=f"Invalid value found: {value}"
                    )
                    return
                
                value = float(value)
                if self.bulk_mode.get() == "weight_to_price":
                    weight_in_grams = self.convert_to_grams(value, self.preferred_unit.get())
                    price = (weight_in_grams / 1000) * float(self.price_per_kg.get())
                    result = {
                        'input': f"{value}{self.preferred_unit.get()}",
                        'result': f"₹{price:.2f}"
                    }
                    self.bulk_result_text.insert('end', f"{value}{self.preferred_unit.get()} → ₹{price:.2f}\n")
                else:
                    weight_in_grams = (value / float(self.price_per_kg.get())) * 1000
                    weight = self.convert_from_grams(weight_in_grams, self.preferred_unit.get())
                    result = {
                        'input': f"₹{value}",
                        'result': f"{weight:.2f}{self.preferred_unit.get()}"
                    }
                    self.bulk_result_text.insert('end', f"₹{value} → {weight:.2f}{self.preferred_unit.get()}\n")
                
                self.bulk_results.append(result)
                
            # Add to history
            history_entry = f"Bulk calculation: {len(values)} items processed\n"
            self.calculation_history.append(history_entry)
            self.update_history()
            self.save_data()
            
        except ValueError as e:
            ttk.Messagebox.show_error(
                title="Error",
                message=f"Error processing values: {str(e)}"
            )

    def export_bulk_results(self):
        """Export bulk calculation results to CSV"""
        if not self.bulk_results:
            ttk.Messagebox.show_warning(
                title="Warning",
                message="No results to export"
            )
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['input', 'result'])
                    writer.writeheader()
                    writer.writerows(self.bulk_results)
                    
                ttk.Messagebox.show_info(
                    title="Success",
                    message="Results exported successfully"
                )
        except Exception as e:
            ttk.Messagebox.show_error(
                title="Error",
                message=f"Error exporting results: {str(e)}"
            )

    def update_text_height(self, event=None):
        """Dynamically update the height of the text widget based on content"""
        # Get current content
        content = self.bulk_input.get('1.0', 'end-1c')
        num_lines = len(content.split('\n'))
        
        # Calculate new height (min 3 lines, max 15 lines)
        new_height = min(max(3, num_lines), 15)
        
        # Update text widget height if changed
        if int(self.bulk_input.cget('height')) != new_height:
            self.bulk_input.configure(height=new_height)
            
            # If content exceeds max height, scroll to the bottom
            if num_lines > 15:
                self.bulk_input.see('end')

    def create_unit_selection_frame(self, parent):
        """Create the unit selection frame"""
        unit_frame = ttk.LabelFrame(
            parent,
            text="Unit Selection",
            padding=15,
            bootstyle="primary"
        )
        unit_frame.pack(fill='x', pady=10)
        
        # Create radio buttons for unit selection
        for unit, info in self.unit_info.items():
            ttk.Radiobutton(
                unit_frame,
                text=info["display"],
                variable=self.preferred_unit,
                value=unit,
                bootstyle="primary-toolbutton"
            ).pack(side='left', expand=True, padx=5)

    def create_weight_to_price_tab(self):
        """Create Weight to Price tab"""
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Weight → Price")
        
        # Input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill='x', pady=10)
        
        # Weight input with unit label
        ttk.Label(
            input_frame,
            text="Enter Weight:",
            font=('Roboto', 12)
        ).pack(side='left', padx=(0, 10))
        
        self.weight_entry = ttk.Entry(
            input_frame,
            font=('Roboto', 12)
        )
        self.weight_entry.pack(side='left', fill='x', expand=True)
        
        # Unit display label
        self.weight_unit_label = ttk.Label(
            input_frame,
            textvariable=self.preferred_unit,
            font=('Roboto', 12)
        )
        self.weight_unit_label.pack(side='left', padx=10)
        
        # Result label
        self.price_result = ttk.Label(
            frame,
            text="Price: ₹0.00",
            font=('Roboto', 14, 'bold')
        )
        self.price_result.pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        # Calculate button
        ttk.Button(
            button_frame,
            text="Calculate",
            command=self.calculate_price,
            bootstyle="primary",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        # Add clear button
        self.add_clear_button(button_frame, [self.weight_entry, self.price_result])

    def create_price_to_weight_tab(self):
        """Create Price to Weight tab"""
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Price → Weight")
        
        # Input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill='x', pady=10)
        
        ttk.Label(
            input_frame,
            text="Enter Price (₹):",
            font=('Roboto', 12)
        ).pack(side='left', padx=(0, 10))
        
        self.price_calc_entry = ttk.Entry(
            input_frame,
            font=('Roboto', 12)
        )
        self.price_calc_entry.pack(side='left', fill='x', expand=True)
        
        # Result label
        self.weight_result = ttk.Label(
            frame,
            text="Weight: 0.00",
            font=('Roboto', 14, 'bold')
        )
        self.weight_result.pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        # Calculate button
        ttk.Button(
            button_frame,
            text="Calculate",
            command=self.calculate_weight,
            bootstyle="primary",
            padding=10
        ).pack(side='left', expand=True, padx=5)
        
        # Clear button
        self.add_clear_button(button_frame, [self.price_calc_entry, self.weight_result])

    def create_bulk_calc_tab(self):
        """Create Bulk Calculations tab with minimal scrollable design"""
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="Bulk Calc")
        
        # Main content frame with fixed height
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill='both', expand=True)
        
        # Compact input section
        input_section = ttk.LabelFrame(content_frame, text="Input Values", padding=(10, 5))
        input_section.pack(fill='x', pady=5)
        
        # Compact mode selection
        self.bulk_mode = ttk.StringVar(value="weight_to_price")
        mode_frame = ttk.Frame(input_section)
        mode_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Radiobutton(
            mode_frame,
            text=f"Weight → Price",
            variable=self.bulk_mode,
            value="weight_to_price",
            bootstyle="primary-toolbutton"
        ).pack(side='left', padx=5)
        
        ttk.Radiobutton(
            mode_frame,
            text=f"Price → Weight",
            variable=self.bulk_mode,
            value="price_to_weight",
            bootstyle="primary-toolbutton"
        ).pack(side='left', padx=5)
        
        # Input text area with scrollbar
        input_frame = ttk.Frame(input_section)
        input_frame.pack(fill='both', expand=True)
        
        input_scroll = ttk.Scrollbar(input_frame)
        input_scroll.pack(side='right', fill='y')
        
        self.bulk_input = ttk.Text(
            input_frame,
            height=4,
            font=('Roboto', 11),
            yscrollcommand=input_scroll.set
        )
        self.bulk_input.pack(fill='both', expand=True)
        input_scroll.config(command=self.bulk_input.yview)
        
        # Placeholder text
        self.bulk_input.insert('1.0', f"Enter values (one per line) in {self.preferred_unit.get()}")
        self.bulk_input.bind('<FocusIn>', lambda e: self.on_input_focus_in())
        self.bulk_input.bind('<FocusOut>', lambda e: self.on_input_focus_out())
        
        # Buttons in a compact row
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(
            button_frame,
            text="Calculate",
            command=self.calculate_bulk,
            bootstyle="primary",
            padding=(10, 5)
        ).pack(side='left', expand=True, padx=2)
        
        ttk.Button(
            button_frame,
            text="Export",
            command=self.export_bulk_results,
            bootstyle="success",
            padding=(10, 5)
        ).pack(side='left', expand=True, padx=2)
        
        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: self.clear_bulk_calc(),
            bootstyle="danger-outline",
            padding=(10, 5)
        ).pack(side='left', expand=True, padx=2)
        
        # Results section
        results_frame = ttk.LabelFrame(content_frame, text="Results", padding=(10, 5))
        results_frame.pack(fill='both', expand=True, pady=5)
        
        # Results text area with scrollbar
        result_scroll = ttk.Scrollbar(results_frame)
        result_scroll.pack(side='right', fill='y')
        
        self.bulk_result_text = ttk.Text(
            results_frame,
            height=6,
            font=('Roboto', 11),
            yscrollcommand=result_scroll.set
        )
        self.bulk_result_text.pack(fill='both', expand=True)
        result_scroll.config(command=self.bulk_result_text.yview)

    def on_input_focus_in(self):
        """Clear placeholder text when input gets focus"""
        if self.bulk_input.get('1.0', 'end-1c') == f"Enter values (one per line) in {self.preferred_unit.get()}":
            self.bulk_input.delete('1.0', 'end')
            self.bulk_input.configure(foreground='black')

    def on_input_focus_out(self):
        """Add placeholder text if input is empty"""
        if not self.bulk_input.get('1.0', 'end-1c').strip():
            self.bulk_input.configure(foreground='gray')
            self.bulk_input.insert('1.0', f"Enter values (one per line) in {self.preferred_unit.get()}")

    def clear_bulk_calc(self):
        """Clear both input and result areas in bulk calculation"""
        self.bulk_input.delete('1.0', 'end')
        self.bulk_result_text.delete('1.0', 'end')
        self.bulk_results = []
        # Reset placeholder text
        self.on_input_focus_out()

    def update_bulk_mode_labels(self, *args):
        """Update the bulk calculation mode labels when unit changes"""
        for child in self.bulk_mode_frame.winfo_children():
            if isinstance(child, ttk.Radiobutton):
                if child.cget('value') == "weight_to_price":
                    child.configure(text=f"Weight ({self.preferred_unit.get()}) → Price (₹)")
                else:
                    child.configure(text=f"Price (₹) → Weight ({self.preferred_unit.get()})")

    def update_results_display(self):
        """Update all result displays with current unit"""
        # Update Weight to Price tab
        if hasattr(self, 'weight_unit_label'):
            self.weight_unit_label.configure(text=self.preferred_unit.get())
        
        # Update Price to Weight tab results if they exist
        if hasattr(self, 'weight_result') and self.weight_result.cget('text') != "Weight: 0.00":
            self.calculate_weight()  # Recalculate with new unit
        
        # Update Bulk calc results if they exist
        if hasattr(self, 'bulk_result_text') and self.bulk_result_text.get(1.0, 'end').strip():
            self.calculate_bulk()  # Recalculate with new unit

    def create_history_frame(self, parent):
        """Create the history toggle button and popup components"""
        # Create toggle button
        self.toggle_button = ttk.Button(
            parent,
            text="Show History",
            command=self.toggle_history_popup,
            bootstyle="info-outline",
            padding=10
        )
        self.toggle_button.pack(fill='x', pady=10)
        
        # Initialize popup state
        self.history_popup_visible = False
        
        # Create frames for blur effect and popup
        self.blur_label = ttk.Label(self.root)
        self.overlay = ttk.Frame(self.root, style='dark.TFrame')
        self.history_popup = ttk.Frame(self.root, style='light.TFrame')
        
        # Create popup content
        self.create_history_popup_content()

    def create_blur_effect(self):
        """Create a semi-transparent overlay instead of blur"""
        try:
            # Get window dimensions
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # Create a dark semi-transparent image
            image = Image.new('RGBA', (width, height), (0, 0, 0, 128))
            
            # Convert to PhotoImage
            return ImageTk.PhotoImage(image)
        
        except Exception as e:
            print(f"Error creating overlay effect: {e}")
            return None

    def toggle_history_popup(self):
        """Toggle the history popup visibility"""
        if self.history_popup_visible:
            self.hide_history_popup()
        else:
            self.show_history_popup()

    def show_history_popup(self):
        """Show the history popup with blur effect"""
        try:
            # Take screenshot and create blur
            self.root.update()
            blur_image = self.create_blur_effect()
            
            if blur_image:
                # Show blur background
                self.blur_label.configure(image=blur_image)
                self.blur_label.image = blur_image  # Keep a reference
                self.blur_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Show semi-transparent overlay
            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Show popup
            self.history_popup.place(
                relx=0.5,
                rely=0.5,
                anchor='center',
                width=400,
                height=500
            )
            
            # Update history content
            self.update_history_content()
            
            # Update state and button text
            self.history_popup_visible = True
            self.toggle_button.configure(text="Hide History")
            
        except Exception as e:
            print(f"Error showing popup: {e}")
            self.show_normal_popup()

    def update_history_content(self):
        """Update the history text content"""
        self.history_text.configure(state='normal')
        self.history_text.delete(1.0, 'end')
        
        if self.calculation_history:
            for entry in self.calculation_history:
                self.history_text.insert('end', entry)
            self.clear_button.configure(state='normal')
        else:
            self.history_text.insert('end', "No calculations yet.")
            self.clear_button.configure(state='disabled')
        
        self.history_text.configure(state='disabled')

    def show_normal_popup(self):
        """Fallback method for showing popup without blur"""
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.history_popup.place(
            relx=0.5,
            rely=0.5,
            anchor='center',
            width=400,
            height=500
        )
        self.update_history_content()
        self.history_popup_visible = True
        self.toggle_button.configure(text="Hide History")

    def hide_history_popup(self):
        """Hide the history popup and remove blur effect"""
        self.blur_label.place_forget()
        self.overlay.place_forget()
        self.history_popup.place_forget()
        self.history_popup_visible = False
        self.toggle_button.configure(text="Show History")

    def create_history_popup_content(self):
        """Create the content for the history popup"""
        # Add padding and style to popup
        content_frame = ttk.Frame(
            self.history_popup,
            padding=20,
            style='popup.TFrame'
        )
        content_frame.pack(fill='both', expand=True)
        
        # Title with enhanced styling
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(
            title_frame,
            text="Calculation History",
            font=('Roboto', 16, 'bold'),
            style="primary.TLabel"
        ).pack(anchor='center')
        
        # History content with improved styling
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Removed bootstyle from Text widget
        self.history_text = ttk.Text(
            text_frame,
            width=40,
            height=15,
            font=('Roboto', 11),
            wrap='word',
            yscrollcommand=scrollbar.set
        )
        self.history_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.history_text.yview)
        
        # Buttons with enhanced styling
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        self.clear_button = ttk.Button(
            button_frame,
            text="Clear History",
            command=self.clear_history,
            bootstyle="danger-outline",
            padding=10
        )
        self.clear_button.pack(side='left', expand=True, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.hide_history_popup,
            bootstyle="secondary",
            padding=10
        ).pack(side='left', expand=True, padx=5)

def main():
    root = ttk.Window()
    app = LightMeasureApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()


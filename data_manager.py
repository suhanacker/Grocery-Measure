import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from data_manager import DataManager # type: ignore

class LightMeasureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Measure")
        self.root.geometry("400x600")
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Load saved data
        saved_data = self.data_manager.load_data()
        
        # Set theme and colors
        self.style = ttk.Style("darkly")
        self.primary_color = "primary"
        
        # Variables
        self.price_per_kg = ttk.StringVar(value=saved_data["default_price"])
        self.preferred_unit = ttk.StringVar(value=saved_data["preferred_unit"])
        self.calculation_history = saved_data["history"]
        
        # Unit conversion factors (to grams)
        self.unit_factors = {
            "g": 1,
            "kg": 1000,
            "lb": 453.592,
            "oz": 28.3495
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        # ... (previous code remains the same until price frame) ...
        
        # Add unit selection
        unit_frame = ttk.LabelFrame(
            main_container, # type: ignore
            text="Unit Selection",
            padding=15,
            bootstyle="primary"
        )
        unit_frame.pack(fill='x', pady=10)
        
        for unit in ["g", "kg", "lb", "oz"]:
            ttk.Radiobutton(
                unit_frame,
                text=unit.upper(),
                variable=self.preferred_unit,
                value=unit,
                bootstyle="primary-toolbutton"
            ).pack(side='left', padx=5, expand=True)
        
        # ... (rest of the widget creation code) ...

    def convert_to_grams(self, value, from_unit):
        return value * self.unit_factors[from_unit]
        
    def convert_from_grams(self, grams, to_unit):
        return grams / self.unit_factors[to_unit]

    def calculate_price(self):
        try:
            if not self.price_per_kg.get():
                ttk.Messagebox.show_error(
                    title="Error",
                    message="Please enter price per kg first"
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
            # Convert input weight to grams
            weight_in_grams = self.convert_to_grams(weight, self.preferred_unit.get())
            price = (weight_in_grams / 1000) * float(self.price_per_kg.get())
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
                    message="Please enter price per kg first"
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
            weight_in_grams = (price / float(self.price_per_kg.get())) * 1000
            # Convert to preferred unit
            weight = self.convert_from_grams(weight_in_grams, self.preferred_unit.get())
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

    def save_data(self):
        self.data_manager.save_data(
            self.calculation_history,
            self.price_per_kg.get(),
            self.preferred_unit.get()
        )

    def clear_history(self):
        self.calculation_history.clear()
        self.history_text.delete(1.0, 'end')
        self.save_data()

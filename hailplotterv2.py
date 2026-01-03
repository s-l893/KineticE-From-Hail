import serial
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend which doesn't require a GUI
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Configuration
COM_PORT = 'COM3'  # Change to your Arduino's COM port
BAUD_RATE = 115200
MAX_SAMPLES = 100
TIMEOUT_SECONDS = 30
USE_DUMMY_DATA = False  # Set to True for testing without Arduino

print("Starting Hailstone Impact Kinetic Energy Visualization...")

# Initialize data lists
times = []
pressures = []
kinetic_energies = []
voltages = []  # Added voltage for completeness

# Collect data from Arduino
if not USE_DUMMY_DATA:
    try:
        print(f"Setting up serial connection on {COM_PORT}...")
        arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print("Waiting for Arduino to initialize...")
        time.sleep(2)  # Wait for the Arduino to initialize
        
        print(f"Reading hailstone impact data (max {MAX_SAMPLES} samples)...")
        start_time = time.time()
        
        while len(times) < MAX_SAMPLES:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                print(f"Received: {line}")  # Debug: print received data
                
                if line.startswith("Time"):  # Skip the header line
                    continue
                    
                try:
                    # Split the CSV data
                    data_parts = line.split(',')
                    if len(data_parts) < 4:
                        print(f"Warning: Incomplete data received: {line}")
                        continue
                        
                    time_data = float(data_parts[0])
                    voltage_data = float(data_parts[1])
                    pressure_data = float(data_parts[2])
                    kinetic_energy_data = float(data_parts[3])
                    
                    # Append data to the lists
                    times.append(time_data)
                    voltages.append(voltage_data)
                    pressures.append(pressure_data)
                    kinetic_energies.append(kinetic_energy_data)
                    
                    print(f"Impact {len(times)}/{MAX_SAMPLES} recorded: KE = {kinetic_energy_data:.2f} J")
                    
                except ValueError as e:
                    print(f"Error parsing data: {e} - Line: {line}")
                    continue
            
            # Check for timeout
            if time.time() - start_time > TIMEOUT_SECONDS:
                print(f"Timeout after {TIMEOUT_SECONDS} seconds. Collected {len(times)} samples.")
                break
                
            # Small delay to prevent CPU hogging
            time.sleep(0.01)
            
        # Close the serial port
        print("Closing serial connection...")
        arduino.close()
    
    except Exception as e:
        print(f"Error connecting to Arduino: {str(e)}")
        print("Falling back to dummy data...")
        USE_DUMMY_DATA = True

# If no data was collected or in dummy mode, create dummy data for testing
if len(times) == 0 or USE_DUMMY_DATA:
    print("Using dummy hailstone impact data for visualization...")
    times = np.linspace(0, 1000, 100)
    # Creating more realistic "spiky" data to simulate impacts
    kinetic_energies = np.zeros(100)
    pressures = np.zeros(100)
    
    # Simulate several hailstone impacts
    for i in range(5):
        impact_point = np.random.randint(10, 90)
        impact_energy = np.random.uniform(30, 100)
        impact_width = np.random.randint(5, 15)
        
        # Create a spike for each impact
        for j in range(max(0, impact_point-impact_width), min(100, impact_point+impact_width)):
            distance = abs(j - impact_point)
            decay = np.exp(-0.3 * distance)
            kinetic_energies[j] = max(kinetic_energies[j], impact_energy * decay)
            pressures[j] = max(pressures[j], impact_energy * 1.5 * decay)

print(f"Data collection complete. Plotting {len(times)} data points.")

# Create the figure and plots using the Agg backend
fig = plt.figure(figsize=(10, 8))
fig.suptitle("Hailstone Impact Analysis", fontsize=16)

# Plot Kinetic Energy vs Time
ax1 = fig.add_subplot(2, 1, 1)
ax1.plot(times, kinetic_energies, label='Kinetic Energy (J)', color='b', linewidth=2)
ax1.set_xlabel('Time (ms)')
ax1.set_ylabel('Kinetic Energy (J)')
ax1.set_title('Hailstone Impact Kinetic Energy vs Time')
ax1.grid(True)

# Add average kinetic energy line
if len(kinetic_energies) > 0:
    avg_ke = np.mean(kinetic_energies)
    max_ke = np.max(kinetic_energies)
    ax1.axhline(y=avg_ke, color='r', linestyle='--', alpha=0.7)
    ax1.text(times[-1]*0.8, avg_ke*1.1, f'Avg: {avg_ke:.2f} J', color='r')
    ax1.text(times[-1]*0.8, max_ke*0.9, f'Max: {max_ke:.2f} J', color='b')

# Plot Pressure Change vs Time
ax2 = fig.add_subplot(2, 1, 2)
ax2.plot(times, pressures, label='Pressure Change (Pa)', color='r', linewidth=2)
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('Pressure Change (Pa)')
ax2.set_title('Pressure Change During Hailstone Impact')
ax2.grid(True)

# Add average pressure line
if len(pressures) > 0:
    avg_pressure = np.mean(pressures)
    max_pressure = np.max(pressures)
    ax2.axhline(y=avg_pressure, color='b', linestyle='--', alpha=0.7)
    ax2.text(times[-1]*0.8, avg_pressure*1.1, f'Avg: {avg_pressure:.2f} Pa', color='b')
    ax2.text(times[-1]*0.8, max_pressure*0.9, f'Max: {max_pressure:.2f} Pa', color='r')

plt.tight_layout()

# Create a Tkinter window to display the plot
root = tk.Tk()
root.title("Hailstone Impact Analysis")
root.geometry("900x700")

# Add an info frame at the top
info_frame = tk.Frame(root, pady=10)
info_frame.pack(side=tk.TOP, fill=tk.X)

if not USE_DUMMY_DATA:
    sample_label = tk.Label(info_frame, 
                           text=f"Recorded {len(times)} hailstone impacts",
                           font=("Arial", 12))
    sample_label.pack()
    
    if len(kinetic_energies) > 0:
        stats_label = tk.Label(info_frame, 
                             text=f"Maximum Kinetic Energy: {np.max(kinetic_energies):.2f} J | Average: {np.mean(kinetic_energies):.2f} J",
                             font=("Arial", 10))
        stats_label.pack()
else:
    dummy_label = tk.Label(info_frame, 
                         text="Using simulated hailstone impact data for demonstration",
                         font=("Arial", 12), fg="blue")
    dummy_label.pack()

# Create a canvas to display the figure
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Add export button
def export_data():
    try:
        filename = f"hailstone_impact_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w') as f:
            f.write("Time(ms),Voltage(V),Pressure(Pa),KineticEnergy(J)\n")
            for i in range(len(times)):
                voltage = voltages[i] if len(voltages) > i else 0
                f.write(f"{times[i]},{voltage},{pressures[i]},{kinetic_energies[i]}\n")
        export_label.config(text=f"Data exported to {filename}")
    except Exception as e:
        export_label.config(text=f"Export error: {str(e)}")

button_frame = tk.Frame(root)
button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

export_button = tk.Button(button_frame, text="Export Data to CSV", command=export_data)
export_button.pack(side=tk.LEFT, padx=20)

export_label = tk.Label(button_frame, text="", fg="green")
export_label.pack(side=tk.LEFT)

close_button = tk.Button(button_frame, text="Close", command=root.destroy)
close_button.pack(side=tk.RIGHT, padx=20)

# Function to handle window close
def on_closing():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
print("Displaying hailstone impact visualization...")
tk.mainloop()

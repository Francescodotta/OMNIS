import numpy as np
import flowio

# Number of events to generate
num_events = 100

# Create random data for FSC-A and SSC-A channels (event data)
# Random values between 0 and 1000 (adjust the range if needed for your case)
event_data = np.random.randint(0, 1000, size=(num_events, 2)).flatten()  # Flattened 1D array

# Define the channel names
channel_names = ['FSC-A', 'SSC-A']

# Optional: You can also define optional channel names (PnS), but we won't use them in this case
opt_channel_names = None

# Create metadata dictionary (optional, can include other FCS-related info)
metadata_dict = {
    'experiment_name': 'Test Experiment',
    'creator': 'AI Model',
    'date': '2025-01-31',
    'compensation_ref': 'compensation_matrix'  # This is where you add the compensation reference
}

# Create a spillover matrix (compensation matrix) for the channels
# This is a simple identity matrix for this example (no spillover), but you can customize it
spillover_matrix = np.eye(len(channel_names)).flatten()

# File handle for the new FCS file (in this case, we write to 'fcs_test_data.fcs')
with open("fcs_test_data.fcs", "wb") as file_handle:
    flowio.create_fcs(file_handle, event_data, channel_names, opt_channel_names, metadata_dict)
    # You may need to include spillover matrix reference in the FCS metadata or attributes depending on your flowio version

print("FCS file 'fcs_test_data.fcs' created successfully!")


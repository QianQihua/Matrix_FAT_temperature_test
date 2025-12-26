import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate Publication-Quality Temperature Plot from CSV and optional Excel.')
parser.add_argument('input_csv', help='Path to the main temperature log CSV file')
parser.add_argument('--external', '-e', help='Path to the external IPT-100S Excel file (optional)', default=None)
parser.add_argument('--output', '-o', help='Path to the output PNG file (optional)', default=None)

args = parser.parse_args()

# Define input/output files based on arguments
input_file = args.input_csv
xls_file = args.external

if args.output:
    output_file = args.output
else:
    # Default output name based on input CSV name
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_plot.png"

if not os.path.exists(input_file):
    print(f"Error: File {input_file} not found.")
    sys.exit(1)

try:
    # Read data
    df = pd.read_csv(input_file)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Read and process Excel file if provided
    df_xls = None
    if xls_file:
        if os.path.exists(xls_file):
            try:
                # Read excel, header is at row 11 (0-indexed) -> row 12 in excel
                df_xls = pd.read_excel(xls_file, header=11)
                
                # Select relevant columns: 鏃堕棿(Time), 鐜娓╁害(Amb), 鎺㈠ご娓╁害(Probe)
                # Using iloc to be safe against encoding issues in headers [1, 2, 4]
                df_xls = df_xls.iloc[:, [1, 2, 4]] 
                df_xls.columns = ['datetime', 'amb_temp', 'probe_temp']
                
                # Parse datetime
                df_xls['datetime'] = pd.to_datetime(df_xls['datetime'])
                
                # Clean temperature columns (remove unit and convert)
                def clean_temp(val):
                    if isinstance(val, str):
                        return float(val.replace('℃', '').replace('C', '').strip())
                    return float(val)

                df_xls['amb_temp'] = df_xls['amb_temp'].apply(clean_temp)
                df_xls['probe_temp'] = df_xls['probe_temp'].apply(clean_temp)
                
                # Merge/Sync data: Find overlapping time range
                start_time = max(df['datetime'].min(), df_xls['datetime'].min())
                end_time = min(df['datetime'].max(), df_xls['datetime'].max())
                
                # Filter both dataframes to the overlapping range
                df = df[(df['datetime'] >= start_time) & (df['datetime'] <= end_time)]
                df_xls = df_xls[(df_xls['datetime'] >= start_time) & (df_xls['datetime'] <= end_time)]
                
                if df.empty or df_xls.empty:
                    print("Warning: No overlapping time range found between the two files. Plotting whatever is available.")
                    
            except Exception as e:
                print(f"Error processing Excel file: {e}")
                df_xls = None
        else:
            print(f"Warning: Excel file {xls_file} not found.")
    
    # Set publication quality parameters
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.linewidth'] = 1.5
    plt.rcParams['xtick.major.width'] = 1.5
    plt.rcParams['ytick.major.width'] = 1.5
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    
    # Plot setup with extra space at bottom for table
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    plt.subplots_adjust(bottom=0.35) # Reserve space for table (slightly more for 5 rows)

    stats_data = []
    columns_table = ['Series', 'Max', 'Max Time', 'Min', 'Min Time', 'Mean', 'Amp (P-P)', 'Var', 'Std Dev']

    def process_and_plot(data_frame, column_name, label_name, color, linestyle='-'):
        if data_frame is not None and column_name in data_frame.columns:
            series = data_frame[column_name]
            if series.empty: return
            
            # Calculate stats
            max_val = series.max()
            max_idx = series.idxmax()
            max_time = data_frame['datetime'].loc[max_idx].strftime('%H:%M:%S')
            
            min_val = series.min()
            min_idx = series.idxmin()
            min_time = data_frame['datetime'].loc[min_idx].strftime('%H:%M:%S')
            
            mean_val = series.mean()
            var_val = series.var()
            std_val = series.std()
            amp_val = max_val - min_val

            # Collect stats
            stats_data.append([
                label_name, 
                f"{max_val:.1f}", max_time,
                f"{min_val:.1f}", min_time,
                f"{mean_val:.2f}",
                f"{amp_val:.1f}",
                f"{var_val:.2f}",
                f"{std_val:.2f}"
            ])
            
            # Plot line
            ax.plot(data_frame['datetime'], series, label=label_name, color=color, linewidth=2, linestyle=linestyle)

    # Plot existing series
    process_and_plot(df, 'cpu_temp', 'CPU Temp', '#d62728', '-')
    process_and_plot(df, 'vulcan_s1_temp', 'Vulcan S1', '#1f77b4', '--')
    process_and_plot(df, 'vulcan_s2_temp', 'Vulcan S2', '#2ca02c', '-.')
    
    # Plot new series from Excel
    if df_xls is not None:
        process_and_plot(df_xls, 'amb_temp', 'Ambient (Ext)', '#ff7f0e', ':')  # Orange, dotted
        process_and_plot(df_xls, 'probe_temp', 'Probe (Ext)', '#9467bd', '-')  # Purple, solid
        
    # X-axis formatting (HH:MM)
    from matplotlib.dates import DateFormatter
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    
    # Fix: Set explicit X-axis limits to match the synchronized data
    # Use the overall min/max of the actual plotted data
    all_dates = pd.concat([df['datetime'], df_xls['datetime']]) if df_xls is not None else df['datetime']
    ax.set_xlim(all_dates.min(), all_dates.max())

    # Set Date in Title
    date_str = df['datetime'].iloc[0].strftime('%Y-%m-%d')
    plt.title(f'Temperature Profile - {date_str}', fontsize=14, pad=15)
    
    plt.xlabel('Time (HH:MM)', fontsize=12, fontweight='bold')
    plt.ylabel('Temperature ($^{\circ}$C)', fontsize=12, fontweight='bold')
    
    # Y-axis adjustment
    # Calculate max across all data
    max_temp = df[['cpu_temp', 'vulcan_s1_temp', 'vulcan_s2_temp']].max().max()
    if df_xls is not None:
        max_xls = df_xls[['amb_temp', 'probe_temp']].max().max()
        max_temp = max(max_temp, max_xls)
        
    plt.ylim(bottom=0, top=max_temp * 1.15)
    
    # Legend
    plt.legend(frameon=True, fancybox=False, edgecolor='black', fontsize=10, loc='best', ncol=2)
    
    # Add Table
    if stats_data:
        table = plt.table(cellText=stats_data,
                          colLabels=columns_table,
                          cellLoc='center',
                          loc='bottom',
                          bbox=[0.0, -0.5, 1.0, 0.35]) # Adjusted for more rows
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
    
    # Save
    plt.savefig(output_file, bbox_inches='tight')
    print(f"Plot saved to {output_file}")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
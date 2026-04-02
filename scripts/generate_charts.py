"""
Chart Generation Module - Supports multiple fonts and data formats
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
import os
import warnings

# Ignore warnings
warnings.filterwarnings('ignore')

# Set custom colors
CUSTOM_COLOR = '#ff5c23'
CHART_COLOR_PALETTE = ['#ff5c23', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

def find_available_font():
    """Find available fonts for chart rendering"""
    # Priority for common fonts
    font_candidates = [
        'DejaVu Sans',
        'Arial',
        'Helvetica',
        'Liberation Sans',
        'Noto Sans CJK SC',
        'WenQuanYi Zen Hei'
    ]

    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font_name in font_candidates:
        if font_name in available_fonts:
            print(f"Found font: {font_name}")
            return font_name

    return 'DejaVu Sans'

def setup_matplotlib_style():
    """Configure Matplotlib style"""
    font_family = find_available_font()

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.sans-serif"] = [font_family]
    plt.rcParams['axes.unicode_minus'] = False  # Handle negative signs
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['text.color'] = '#333333'
    plt.rcParams['axes.labelcolor'] = '#333333'
    plt.rcParams['xtick.color'] = '#333333'
    plt.rcParams['ytick.color'] = '#333333'
    plt.rcParams['grid.color'] = '#e0e0e0'
    plt.rcParams['grid.linestyle'] = '--'
    plt.rcParams['axes.edgecolor'] = '#cccccc'
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False

def extract_chart_data(data, x_key, y_key, data_keys_mapping=None):
    """
    Extract data needed for charts from API response
    Supports multiple data formats:
    1. Direct list: [{"key1": val1, "key2": val2}, ...]
    2. {"data": {"items": [...]}} format
    3. {"data": [...]} format
    4. {"items": [...]} format
    """
    if not data:
        return None

    # Handle dictionary wrapping
    if isinstance(data, dict):
        # Try various common wrapping formats
        if "data" in data:
            inner = data["data"]
            if isinstance(inner, dict):
                if "items" in inner:
                    data = inner["items"]
                elif "metrics" in inner:
                    data = inner["metrics"]
                elif isinstance(inner, list):
                    data = inner
            elif isinstance(inner, list):
                data = inner
        elif "items" in data:
            data = data["items"]
        elif isinstance(data, list):
            data = data

    if not isinstance(data, list):
        print(f"Warning: Data is not a list after extraction: {type(data)}")
        return None

    if len(data) == 0:
        return None

    # Apply key mapping if provided
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue

        x_val = None
        y_val = None

        if data_keys_mapping:
            # Convert fields using mapping
            for source_key, target_key in data_keys_mapping.items():
                if source_key in item:
                    if target_key == x_key:
                        x_val = item[source_key]
                    elif target_key == y_key:
                        # Try to convert value to float
                        try:
                            y_val = float(item[source_key])
                        except (ValueError, TypeError):
                            y_val = 0
        else:
            # Use specified keys directly
            x_val = item.get(x_key)
            y_val = item.get(y_key)
            # Try to convert y value to float
            if y_val is not None:
                try:
                    y_val = float(y_val)
                except (ValueError, TypeError):
                    # If string, try conversion
                    if isinstance(y_val, str):
                        if y_val.isdigit():
                            y_val = float(y_val)
                        else:
                            y_val = None

        if x_val is not None and y_val is not None:
            result.append((str(x_val), y_val))

    return result if result else None

def generate_bar_chart(data, x_key, y_key, title, xlabel, ylabel, filename, color=None):
    """Generate bar chart and save as PNG"""
    if color is None:
        color = CUSTOM_COLOR

    # Set style
    setup_matplotlib_style()

    # Extract chart data
    chart_data = extract_chart_data(data, x_key, y_key)

    if not chart_data:
        print(f"Warning: No valid data for bar chart {filename}")
        return None

    # Limit number of items (max 15)
    chart_data = chart_data[:15]

    x_values, y_values = zip(*chart_data)

    # Create chart
    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(range(len(x_values)), y_values, color=color, edgecolor='white', linewidth=0.5)

    # Set labels
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Set x-axis ticks
    ax.set_xticks(range(len(x_values)))

    # Handle long labels (truncate or rotate)
    display_labels = []
    for label in x_values:
        if len(str(label)) > 20:
            display_labels.append(str(label)[:17] + '...')
        else:
            display_labels.append(str(label))

    ax.set_xticklabels(display_labels, rotation=45, ha='right', fontsize=10)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, y_values)):
        height = bar.get_height()
        ax.annotate(f'{val:.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9, color='#333333')

    # Aesthetics
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Save chart
    output_path = os.path.join(os.path.dirname(__file__), "..", "templates", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    print(f"Generated chart: {output_path}")
    return output_path

def generate_horizontal_bar_chart(data, x_key, y_key, title, xlabel, ylabel, filename, color=None):
    """Generate horizontal bar chart and save as PNG
    Args:
        data: Data
        x_key: Numeric field name (displayed on x-axis)
        y_key: Categorical field name (displayed on y-axis)
    """
    if color is None:
        color = CUSTOM_COLOR

    setup_matplotlib_style()

    # Swap x_key and y_key because extract_chart_data expects x_key as category, y_key as numeric
    chart_data = extract_chart_data(data, y_key, x_key)

    if not chart_data:
        print(f"Warning: No valid data for horizontal bar chart {filename}")
        return None

    chart_data = chart_data[:15]

    # Sort by value
    chart_data.sort(key=lambda x: x[1], reverse=True)

    y_values_sorted = [x[0] for x in chart_data]
    x_values_sorted = [x[1] for x in chart_data]

    fig, ax = plt.subplots(figsize=(10, max(6, len(chart_data) * 0.5)))

    bars = ax.barh(range(len(y_values_sorted)), x_values_sorted, color=color, edgecolor='white', linewidth=0.5)

    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    ax.set_yticks(range(len(y_values_sorted)))

    # Truncate long labels
    display_labels = []
    for label in y_values_sorted:
        if len(str(label)) > 30:
            display_labels.append(str(label)[:27] + '...')
        else:
            display_labels.append(str(label))

    ax.set_yticklabels(display_labels, fontsize=10)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, x_values_sorted)):
        width = bar.get_width()
        ax.annotate(f'{val:.0f}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0),
                    textcoords="offset points",
                    ha='left', va='center',
                    fontsize=9, color='#333333')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    output_path = os.path.join(os.path.dirname(__file__), "..", "templates", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    print(f"Generated horizontal bar chart: {output_path}")
    return output_path

def generate_pie_chart(data, label_key, value_key, title, filename, color=None):
    """Generate pie chart"""
    if color is None:
        color = CHART_COLOR_PALETTE

    setup_matplotlib_style()

    chart_data = extract_chart_data(data, label_key, value_key)

    if not chart_data:
        print(f"Warning: No valid data for pie chart {filename}")
        return None

    chart_data = chart_data[:8]  # Limit items

    labels = [str(x[0])[:20] for x in chart_data]
    sizes = [x[1] for x in chart_data]

    fig, ax = plt.subplots(figsize=(10, 8))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=color[:len(sizes)],
        wedgeprops=dict(edgecolor='white', linewidth=2)
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)

    # Add legend
    ax.legend(wedges, labels, title="", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_path = os.path.join(os.path.dirname(__file__), "..", "templates", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    print(f"Generated pie chart: {output_path}")
    return output_path

# Example usage
if __name__ == '__main__':
    setup_matplotlib_style()

    print("Testing chart generation...")

    # Sample data
    sample_citation_domains = {
        "data": {
            "items": [
                {"domain": "techcrunch.com", "citationCount": 250},
                {"domain": "searchengineland.com", "citationCount": 180},
                {"domain": "forbes.com", "citationCount": 120},
                {"domain": "venturebeat.com", "citationCount": 95},
                {"domain": "wired.com", "citationCount": 70}
            ]
        }
    }

    # Test bar chart
    path = generate_bar_chart(
        sample_citation_domains,
        x_key="domain",
        y_key="citationCount",
        title="Top Citation Domains",
        xlabel="Domain",
        ylabel="Citations",
        filename="citation_domains_bar_chart.png"
    )
    print(f"Generated: {path}")

    # Test horizontal bar chart
    path = generate_horizontal_bar_chart(
        sample_citation_domains,
        x_key="domain",
        y_key="citationCount",
        title="Citation Domain Ranking",
        xlabel="Citations",
        ylabel="Domain",
        filename="citation_domains_horizontal.png"
    )
    print(f"Generated: {path}")

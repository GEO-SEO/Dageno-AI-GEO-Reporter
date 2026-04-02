"""
图表生成模块 - 支持中文字体和多种数据格式
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
import os
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 设置自定义颜色
CUSTOM_COLOR = '#ff5c23'
CHART_COLOR_PALETTE = ['#ff5c23', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c']

def find_chinese_font():
    """查找可用的中文字体"""
    # 优先使用 Noto Sans CJK SC，然后是文泉驿系列
    font_candidates = [
        'Noto Sans CJK SC',
        'WenQuanYi Zen Hei',
        'WenQuanYi Micro Hei',
        'SimHei',
        'DejaVu Sans'
    ]

    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font_name in font_candidates:
        if font_name in available_fonts:
            print(f"Found Chinese font: {font_name}")
            return font_name

    # 打印一些可用字体用于调试
    cjk_fonts = [f.name for f in fm.fontManager.ttflist if 'CJK' in f.name or 'WenQuan' in f.name]
    if cjk_fonts:
        print(f"Available CJK fonts: {cjk_fonts[:5]}")
        return cjk_fonts[0]

    return 'DejaVu Sans'

def setup_matplotlib_style():
    """配置 Matplotlib 样式"""
    chinese_font = find_chinese_font()

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams["font.family"] = chinese_font
    plt.rcParams["font.sans-serif"] = [chinese_font]
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
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
    从 API 返回的数据中提取图表需要的数据
    支持多种数据格式：
    1. 直接是列表: [{"key1": val1, "key2": val2}, ...]
    2. {"data": {"items": [...]}} 格式
    3. {"data": [...]} 格式
    4. {"items": [...]} 格式
    """
    if not data:
        return None

    # 处理字典包装
    if isinstance(data, dict):
        # 尝试多种常见的包装格式
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

    # 如果提供了 key 映射，尝试转换字段名
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue

        x_val = None
        y_val = None

        if data_keys_mapping:
            # 使用映射转换字段
            for source_key, target_key in data_keys_mapping.items():
                if source_key in item:
                    if target_key == x_key:
                        x_val = item[source_key]
                    elif target_key == y_key:
                        # 尝试将值转换为数字
                        try:
                            y_val = float(item[source_key])
                        except (ValueError, TypeError):
                            y_val = 0
        else:
            # 直接使用指定的 key
            x_val = item.get(x_key)
            y_val = item.get(y_key)
            # 尝试转换 y 值为数字
            if y_val is not None:
                try:
                    y_val = float(y_val)
                except (ValueError, TypeError):
                    # 如果是字符串，尝试转换
                    if isinstance(y_val, str):
                        if y_val.isdigit():
                            y_val = float(y_val)
                        else:
                            y_val = None

        if x_val is not None and y_val is not None:
            result.append((str(x_val), y_val))

    return result if result else None

def generate_bar_chart(data, x_key, y_key, title, xlabel, ylabel, filename, color=None):
    """生成条形图并保存为 PNG"""
    if color is None:
        color = CUSTOM_COLOR

    # 设置样式
    setup_matplotlib_style()

    # 提取图表数据
    chart_data = extract_chart_data(data, x_key, y_key)

    if not chart_data:
        print(f"Warning: No valid data for bar chart {filename}")
        return None

    # 限制显示的条目数量（最多15个）
    chart_data = chart_data[:15]

    x_values, y_values = zip(*chart_data)

    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(range(len(x_values)), y_values, color=color, edgecolor='white', linewidth=0.5)

    # 设置标签
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # 设置 x 轴标签
    ax.set_xticks(range(len(x_values)))

    # 处理长标签（截断或旋转）
    display_labels = []
    for label in x_values:
        if len(str(label)) > 20:
            display_labels.append(str(label)[:17] + '...')
        else:
            display_labels.append(str(label))

    ax.set_xticklabels(display_labels, rotation=45, ha='right', fontsize=10)

    # 在条形上添加数值标签
    for i, (bar, val) in enumerate(zip(bars, y_values)):
        height = bar.get_height()
        ax.annotate(f'{val:.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9, color='#333333')

    # 美化
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(os.path.dirname(__file__), "..", "templates", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    print(f"Generated chart: {output_path}")
    return output_path

def generate_horizontal_bar_chart(data, x_key, y_key, title, xlabel, ylabel, filename, color=None):
    """生成水平条形图并保存为 PNG
    Args:
        data: 数据
        x_key: 数值型字段名 (将在 x 轴显示)
        y_key: 类别型字段名 (将在 y 轴显示)
    """
    if color is None:
        color = CUSTOM_COLOR

    setup_matplotlib_style()

    # 交换 x_key 和 y_key，因为 extract_chart_data 期望 x_key 是类别，y_key 是数值
    chart_data = extract_chart_data(data, y_key, x_key)

    if not chart_data:
        print(f"Warning: No valid data for horizontal bar chart {filename}")
        return None

    chart_data = chart_data[:15]

    # 按值排序
    chart_data.sort(key=lambda x: x[1], reverse=True)

    y_values_sorted = [x[0] for x in chart_data]
    x_values_sorted = [x[1] for x in chart_data]

    fig, ax = plt.subplots(figsize=(10, max(6, len(chart_data) * 0.5)))

    bars = ax.barh(range(len(y_values_sorted)), x_values_sorted, color=color, edgecolor='white', linewidth=0.5)

    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    ax.set_yticks(range(len(y_values_sorted)))

    # 截断长标签
    display_labels = []
    for label in y_values_sorted:
        if len(str(label)) > 30:
            display_labels.append(str(label)[:27] + '...')
        else:
            display_labels.append(str(label))

    ax.set_yticklabels(display_labels, fontsize=10)

    # 添加数值标签
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
    """生成饼图"""
    if color is None:
        color = CHART_COLOR_PALETTE

    setup_matplotlib_style()

    chart_data = extract_chart_data(data, label_key, value_key)

    if not chart_data:
        print(f"Warning: No valid data for pie chart {filename}")
        return None

    chart_data = chart_data[:8]  # 限制数量

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

    # 添加图例
    ax.legend(wedges, labels, title="", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_path = os.path.join(os.path.dirname(__file__), "..", "templates", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    print(f"Generated pie chart: {output_path}")
    return output_path

# 示例用法
if __name__ == '__main__':
    setup_matplotlib_style()

    print("Testing chart generation...")

    # 测试数据
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

    # 测试条形图
    path = generate_bar_chart(
        sample_citation_domains,
        x_key="domain",
        y_key="citationCount",
        title="热门引用域名",
        xlabel="域名",
        ylabel="引用次数",
        filename="citation_domains_bar_chart.png"
    )
    print(f"Generated: {path}")

    # 测试水平条形图
    path = generate_horizontal_bar_chart(
        sample_citation_domains,
        x_key="domain",
        y_key="citationCount",
        title="引用域名排名",
        xlabel="引用次数",
        ylabel="域名",
        filename="citation_domains_horizontal.png"
    )
    print(f"Generated: {path}")
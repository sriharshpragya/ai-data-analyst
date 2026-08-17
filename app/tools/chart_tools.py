"""
Chart generation tools for the Data Analyst Agent.
Uses matplotlib to create business-appropriate visualizations.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from typing import List, Optional
import structlog

from app.config import Config

logger = structlog.get_logger()

# Colors
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#3D9970',
    'warning': '#FF851B',
    'danger': '#FF4136',
}

CHART_COLORS = [
    COLORS['primary'], COLORS['secondary'], COLORS['accent'],
    COLORS['success'], COLORS['warning'], '#7FDBFF', '#B10DC9', '#01FF70',
]


def _generate_filename(chart_type: str, title: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
    return f"{Config.CHARTS_DIR}/{chart_type}_{safe_title}_{timestamp}.png"


def _format_number(value: float, position=None) -> str:
    if abs(value) >= 10000000:
        return f'₹{value/10000000:.1f}Cr'
    elif abs(value) >= 100000:
        return f'₹{value/100000:.1f}L'
    elif abs(value) >= 1000:
        return f'₹{value/1000:.0f}K'
    else:
        return f'₹{value:.0f}'


def _setup_chart_style():
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (12, 6),
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': '#E5E5E5',
        'grid.linestyle': '-',
        'grid.linewidth': 0.5,
        'font.size': 11,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
    })


def _create_bar_chart(data, title, x_label, y_label, is_currency=True):
    labels = [item['label'] for item in data]
    values = [item['value'] for item in data]
    
    fig, ax = plt.subplots()
    bars = ax.bar(labels, values, color=COLORS['primary'], edgecolor='white', linewidth=1.5)
    
    for bar, value in zip(bars, values):
        height = bar.get_height()
        label = _format_number(value) if is_currency else f'{value:,.0f}'
        ax.text(bar.get_x() + bar.get_width() / 2, height, label,
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_title(title, pad=20)
    ax.set_xlabel(x_label, labelpad=10)
    ax.set_ylabel(y_label, labelpad=10)
    
    if is_currency:
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(_format_number))
    else:
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    if len(labels) > 5 or any(len(str(l)) > 10 for l in labels):
        plt.xticks(rotation=30, ha='right')
    
    plt.tight_layout()
    return fig


def _create_horizontal_bar_chart(data, title, x_label, y_label, is_currency=True):
    labels = [item['label'] for item in data][::-1]
    values = [item['value'] for item in data][::-1]
    
    fig, ax = plt.subplots()
    bars = ax.barh(labels, values, color=COLORS['primary'], edgecolor='white', linewidth=1.5)
    
    for bar, value in zip(bars, values):
        width = bar.get_width()
        label = _format_number(value) if is_currency else f'{value:,.0f}'
        ax.text(width, bar.get_y() + bar.get_height() / 2, f' {label}',
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    ax.set_title(title, pad=20)
    ax.set_xlabel(x_label, labelpad=10)
    ax.set_ylabel(y_label, labelpad=10)
    
    if is_currency:
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(_format_number))
    else:
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    plt.tight_layout()
    return fig


def _create_line_chart(data, title, x_label, y_label, is_currency=True):
    labels = [item['label'] for item in data]
    values = [item['value'] for item in data]
    
    fig, ax = plt.subplots()
    ax.plot(labels, values, marker='o', linewidth=2.5, markersize=8,
            color=COLORS['primary'], markerfacecolor='white', markeredgewidth=2)
    ax.fill_between(range(len(labels)), values, alpha=0.15, color=COLORS['primary'])
    
    for i, (label, value) in enumerate(zip(labels, values)):
        formatted = _format_number(value) if is_currency else f'{value:,.0f}'
        ax.annotate(formatted, (i, value), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=9, fontweight='bold')
    
    ax.set_title(title, pad=20)
    ax.set_xlabel(x_label, labelpad=10)
    ax.set_ylabel(y_label, labelpad=10)
    
    if is_currency:
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(_format_number))
    else:
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    if len(labels) > 5 or any(len(str(l)) > 10 for l in labels):
        plt.xticks(rotation=30, ha='right')
    
    plt.tight_layout()
    return fig


def _create_pie_chart(data, title):
    labels = [item['label'] for item in data]
    values = [item['value'] for item in data]
    total = sum(values)
    
    def make_autopct(values):
        def my_autopct(pct):
            val = pct * total / 100
            return f'{pct:.1f}%\n{_format_number(val)}'
        return my_autopct
    
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=CHART_COLORS[:len(values)],
        autopct=make_autopct(values), startangle=90,
        wedgeprops=dict(edgecolor='white', linewidth=2),
        textprops=dict(fontsize=11)
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    ax.set_title(title, pad=20)
    plt.tight_layout()
    return fig


def create_chart(
    chart_type: str,
    title: str,
    data: List[dict],
    x_label: Optional[str] = "",
    y_label: Optional[str] = "",
    is_currency: bool = True,
) -> dict:
    """Create a chart from data."""
    logger.info("chart_creation_requested", chart_type=chart_type, title=title,
                data_points=len(data) if data else 0)
    
    if not data:
        return {"error": "empty_data", "message": "Cannot create chart with no data"}
    
    if chart_type not in ['bar', 'horizontal_bar', 'line', 'pie']:
        return {
            "error": "invalid_chart_type",
            "message": f"Chart type '{chart_type}' not supported",
            "supported_types": ['bar', 'horizontal_bar', 'line', 'pie'],
        }
    
    for i, item in enumerate(data):
        if not isinstance(item, dict) or 'label' not in item or 'value' not in item:
            return {"error": "invalid_data_format",
                    "message": f"Data item {i} invalid"}
        try:
            item['value'] = float(item['value'])
        except (ValueError, TypeError):
            return {"error": "invalid_value",
                    "message": f"Non-numeric value: {item['value']}"}
    
    if len(data) > 20:
        data = data[:20]
    
    try:
        _setup_chart_style()
        
        if chart_type == 'bar':
            fig = _create_bar_chart(data, title, x_label, y_label, is_currency)
        elif chart_type == 'horizontal_bar':
            fig = _create_horizontal_bar_chart(data, title, x_label, y_label, is_currency)
        elif chart_type == 'line':
            fig = _create_line_chart(data, title, x_label, y_label, is_currency)
        elif chart_type == 'pie':
            fig = _create_pie_chart(data, title)
        
        filename = _generate_filename(chart_type, title)
        fig.savefig(filename, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Return relative path (for web serving)
        relative_path = filename.replace(str(Config.CHARTS_DIR), 'charts')
        
        return {
            "success": True,
            "chart_type": chart_type,
            "title": title,
            "file_path": filename,
            "url": f"/{relative_path}",
            "data_points": len(data),
        }
    
    except Exception as e:
        logger.error("chart_creation_error", error=str(e))
        return {"error": "chart_creation_failed",
                "message": f"{type(e).__name__}: {str(e)}"}


create_chart_schema = {
    "type": "function",
    "function": {
        "name": "create_chart",
        "description": (
            "Create a chart visualization from data. "
            "Chart types: 'bar' (comparisons), 'horizontal_bar' (long labels), "
            "'line' (trends over time), 'pie' (distributions/shares)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "horizontal_bar", "line", "pie"],
                    "description": "Type of chart",
                },
                "title": {"type": "string", "description": "Chart title"},
                "data": {
                    "type": "array",
                    "description": "List of data points",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "number"},
                        },
                        "required": ["label", "value"],
                    },
                },
                "x_label": {"type": "string", "description": "X-axis label"},
                "y_label": {"type": "string", "description": "Y-axis label"},
                "is_currency": {
                    "type": "boolean",
                    "description": "Format as ₹ (default: true)",
                },
            },
            "required": ["chart_type", "title", "data"],
        },
    },
}

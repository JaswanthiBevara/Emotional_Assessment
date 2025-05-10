import matplotlib.pyplot as plt
import numpy as np  # Needed for angle calculations
from io import BytesIO
import base64

def generate_pie_chart(data, title):
    plt.figure(figsize=(7, 7))
    values = list(data.values())
    labels = list(data.keys())
    
    # Generate the pie chart without default labels
    wedges, _, autotexts = plt.pie(
        values,
        labels=None,
        autopct='%1.1f%%',
        startangle=140,
        textprops=dict(color="white")
    )

    # Draw custom labels outside the pie using arrows
    for i, wedge in enumerate(wedges):
        angle = (wedge.theta2 + wedge.theta1) / 2.0
        x = np.cos(np.radians(angle))
        y = np.sin(np.radians(angle))

        horizontalalignment = 'left' if x >= 0 else 'right'
        connectionstyle = f"angle,angleA=0,angleB={angle}"

        plt.annotate(
            labels[i],
            xy=(x * 0.7, y * 0.7),
            xytext=(x * 1.2, y * 1.2),
            ha=horizontalalignment,
            va='center',
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.8),
            arrowprops=dict(arrowstyle="-", connectionstyle=connectionstyle, color='gray')
        )

    # Optional title
    # plt.title(title)

    return _convert_plot_to_base64()



def generate_bar_chart(data, title):
    plt.figure(figsize=(6, 4))
    emotions = list(data.keys())
    percentages = list(data.values())

    bars = plt.bar(emotions, percentages, color='skyblue')
    plt.ylabel('Percentage')
    # plt.title(title)  # Removed as per your requirement

    # Add percentage labels on top of each bar
    for bar, value in zip(bars, percentages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f'{value}%',
                 ha='center', va='bottom', fontsize=9)

    return _convert_plot_to_base64()


def _convert_plot_to_base64():
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return f"data:image/png;base64,{image_base64}" 

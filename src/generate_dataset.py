import matplotlib.pyplot as plt
import os
import random
import numpy as np

# --- Tự động chuyển về thư mục gốc chart2code/ ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)

# --- CÀI ĐẶT ---
TOTAL_SAMPLES = 2500 # Tạo 500 mẫu 
IMAGE_DIR = "data/images"
CODE_DIR  = "data/codes"
# -----------------

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(CODE_DIR, exist_ok=True)

print(f"Đang tạo {TOTAL_SAMPLES} mẫu (bao gồm 4 loại biểu đồ)...")

# === CÁC LOẠI BIỂU ĐỒ ===

def generate_bar_chart(index):
    """Tạo biểu đồ cột"""
    num_bars = random.randint(3, 7)
    data = np.random.randint(10, 100, size=num_bars)
    labels = [f'Label {chr(65 + j)}' for j in range(num_bars)]
    colors = random.sample(['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'orange'], k=num_bars)
    
    plt.figure() 
    plt.bar(labels, data, color=colors)
    plt.title(f'Bar Chart {index+1}')
    plt.ylabel('Values')
    
    image_filename = f'bar_chart_{index+1}.png'
    image_path = os.path.join(IMAGE_DIR, image_filename)
    plt.savefig(image_path)
    plt.close() 
    
    code_string = f"""
import matplotlib.pyplot as plt

labels = {labels}
data = {list(data)} 
colors = {colors}

plt.bar(labels, data, color=colors)
plt.title('Bar Chart {index+1}')
plt.ylabel('Values')
plt.show()
"""
    code_filename = f'bar_chart_{index+1}.txt'
    code_path = os.path.join(CODE_DIR, code_filename)
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(code_string)

def generate_line_chart(index):
    """Tạo biểu đồ đường """
    num_points = random.randint(5, 12)
    x = np.arange(num_points)
    y = np.random.randint(10, 100, size=num_points) + np.random.randn(num_points) * 5 # Thêm nhiễu
    marker = random.choice(['o', 's', '^', '*'])
    line_style = random.choice(['-', '--', '-.', ':'])
    color = random.choice(['blue', 'green', 'red', 'purple', 'orange'])
    
    plt.figure()
    plt.plot(x, y, marker=marker, linestyle=line_style, color=color)
    plt.title(f'Line Chart {index+1}')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.grid(True) # Thêm lưới
    
    image_filename = f'line_chart_{index+1}.png'
    image_path = os.path.join(IMAGE_DIR, image_filename)
    plt.savefig(image_path)
    plt.close()
    
    code_string = f"""
import matplotlib.pyplot as plt
import numpy as np
x = {list(x)}
y = {list(y)} 
marker = '{marker}'
linestyle = '{line_style}'
color = '{color}'

plt.plot(x, y, marker=marker, linestyle=linestyle, color=color)
plt.title('Line Chart {index+1}')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.grid(True)
plt.show()
"""
    code_filename = f'line_chart_{index+1}.txt'
    code_path = os.path.join(CODE_DIR, code_filename)
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(code_string)

def generate_pie_chart(index):
    """Tạo biểu đồ tròn """
    num_slices = random.randint(3, 6)
    sizes = np.random.randint(10, 100, size=num_slices)
    labels = [f'Part {chr(65 + j)}' for j in range(num_slices)]
    # Chọn màu không trùng lặp
    colors = random.sample(['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'lightgreen', 'pink'], k=num_slices)
    explode = [0] * num_slices
    if random.random() > 0.5: # Thỉnh thoảng tách 1 miếng ra
        explode[random.randint(0, num_slices - 1)] = 0.1
        
    plt.figure()
    plt.pie(sizes, explode=tuple(explode), labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    plt.title(f'Pie Chart {index+1}')
    plt.axis('equal') # Đảm bảo hình tròn

    image_filename = f'pie_chart_{index+1}.png'
    image_path = os.path.join(IMAGE_DIR, image_filename)
    plt.savefig(image_path)
    plt.close()
    
    code_string = f"""
import matplotlib.pyplot as plt

sizes = {list(sizes)}
labels = {labels}
colors = {colors}
explode = {tuple(explode)}

plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
plt.title('Pie Chart {index+1}')
plt.axis('equal') 
plt.show()
"""
    code_filename = f'pie_chart_{index+1}.txt'
    code_path = os.path.join(CODE_DIR, code_filename)
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(code_string)

def generate_scatter_plot(index):
    """Tạo biểu đồ phân tán """
    num_points = random.randint(20, 100)
    x = np.random.rand(num_points) * 100
    y = np.random.rand(num_points) * 100
    sizes = np.random.randint(10, 200, size=num_points)
    colors = np.random.rand(num_points) # Màu theo thang độ
    marker = random.choice(['o', 's', '^', 'D'])
    
    plt.figure()
    plt.scatter(x, y, s=sizes, c=colors, marker=marker, alpha=0.7, cmap='viridis') # Thêm colormap
    plt.colorbar(label='Color Intensity') # Thêm thanh màu
    plt.title(f'Scatter Plot {index+1}')
    plt.xlabel('X Value')
    plt.ylabel('Y Value')
    plt.grid(True)

    image_filename = f'scatter_chart_{index+1}.png'
    image_path = os.path.join(IMAGE_DIR, image_filename)
    plt.savefig(image_path)
    plt.close()
    
    code_string = f"""
import matplotlib.pyplot as plt
import numpy as np # Cần numpy

x = {list(x)}
y = {list(y)}
sizes = {list(sizes)}
colors = {list(colors)} # Đây là giá trị màu, không phải tên màu
marker = '{marker}'

plt.scatter(x, y, s=sizes, c=colors, marker=marker, alpha=0.7, cmap='viridis')
plt.colorbar(label='Color Intensity') 
plt.title('Scatter Plot {index+1}')
plt.xlabel('X Value')
plt.ylabel('Y Value')
plt.grid(True)
plt.show()
"""
    code_filename = f'scatter_chart_{index+1}.txt'
    code_path = os.path.join(CODE_DIR, code_filename)
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(code_string)

# === TẠO DATASET ===
chart_generators = [generate_bar_chart, generate_line_chart, generate_pie_chart, generate_scatter_plot]

for i in range(TOTAL_SAMPLES):
    chosen_generator = random.choice(chart_generators)
    chosen_generator(i)
    
    # tiến độ
    if (i+1) % 50 == 0: 
        print(f"Đã tạo xong {i+1} / {TOTAL_SAMPLES} mẫu...")

print("HOÀN TẤT!")
print(f"Lưu trong thư mục '{IMAGE_DIR}' và '{CODE_DIR}'.")
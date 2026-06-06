import glob

for ui_file in glob.glob("view/*.ui"):
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("QTabWidget::TabShape::Rounded", "Rounded")
    content = content.replace("QTabWidget::TabShape::Triangular", "Triangular")
    content = content.replace("QTabWidget::TabPosition::", "")
    
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Corregido: {ui_file}")
import shutil

# Copy enhanced files
shutil.copy2(
    r'C:\Users\NADEEM\Downloads\Quotes Images\image_generator_enhanced.py',
    r'C:\Users\NADEEM\Downloads\Quotes Images\scripts\image_generator.py'
)

shutil.copy2(
    r'C:\Users\NADEEM\Downloads\Quotes Images\dashboard_enhanced.py',
    r'C:\Users\NADEEM\Downloads\Quotes Images\scripts\dashboard.py'
)

print("✅ Files copied successfully!")
print("\nNow run: python scripts\\dashboard.py")

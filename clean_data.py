import pandas as pd
import re

# Read your original file
df = pd.read_excel('Table1 (2).xls', header=1)

# Clean up the footnote letters attached to the numbers
def clean_val(x):
    if pd.isna(x):
        return x
    if isinstance(x, str):
        cleaned = re.sub(r'[^\d.-]', '', x)
        try:
            return float(cleaned)
        except:
            return None
    return x

for col in df.columns[1:]:
    df[col] = df[col].apply(clean_val)

# Rename columns so they work smoothly with the app
new_cols = [c.strip().lower().replace(', ', '_').replace(' & ', '_').replace(' ', '_') for c in df.columns]
df.columns = new_cols
df['country'] = df['country'].astype(str).str.strip().str.title()

# Save the new file!
df.to_excel('Cleaned_Table1_Full_Elasticity.xlsx', index=False)
print("Success! Cleaned_Table1_Full_Elasticity.xlsx has been created in your folder.")

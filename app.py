import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Data setup
data = {
    "Category": [
        "Food",
        "Housing",
        "Apparel",
        "Transportation",
        "Entertainment",
        "Healthcare",
    ],
    "Type": ["Food", "Non-Food", "Non-Food", "Non-Food", "Non-Food", "Non-Food"],
    "Elasticity": [0.45, 0.85, 1.25, 1.10, 1.60, 0.75],
    "Good Type": [
        "Necessity",
        "Necessity",
        "Luxury",
        "Luxury",
        "Luxury",
        "Necessity",
    ],
}

df = pd.DataFrame(data)

# 1. Assign colors: Highlight Food, alternate light and dark grays for non-food categories
colors = []
gray_toggle = False
for cat_type in df["Type"]:
    if cat_type.lower() == "food":
        colors.append("#FF9999")  # Highlight accent for Food
    else:
        colors.append("#D3D3D3" if gray_toggle else "#707070")  # Alternating grays
        gray_toggle = not gray_toggle

# Create figure and axes layout
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(8, 8), gridspec_kw={"height_ratios": [3, 1.2]}
)

# Pie Chart rendering
ax1.pie(
    df["Elasticity"],
    labels=df["Category"],
    colors=colors,
    autopct="%1.1f%%",
    startangle=140,
)
ax1.set_title("Expenditure & Elasticity Breakdown", fontsize=14, pad=15)

# 2. Renamed table title to 'Income Elasticity'
ax2.axis("off")
ax2.set_title("Income Elasticity", fontsize=12, fontweight="bold", pad=10)

# Extract table contents and column headers
table_data = df[["Category", "Elasticity", "Good Type"]].values.tolist()
col_labels = ["Category", "Elasticity", "Good Type"]

# 3. Render table with centered text alignment
table = ax2.table(
    cellText=table_data, colLabels=col_labels, loc="center", cellLoc="center"
)

# 4. Decrease column width so table fits contents instead of stretching full width
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(0.65, 1.2)

plt.tight_layout()

# Render in Streamlit (or use plt.show() if running as a standalone script)
if __name__ == "__main__":
    st.pyplot(fig)

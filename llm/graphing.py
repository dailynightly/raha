import matplotlib.pyplot as plt
import pandas as pd

# Sample DataFrame
data = {'Categories': ['Category1', 'Category2', 'Category3'],
        'Values': [80, 50, 95]}  # These are the percentages
df = pd.DataFrame(data)

# Plotting
ax = df.plot(x='Categories', y='Values', kind='bar', legend=False)

# Add a line at 100%
ax.axhline(100, color='gray', linewidth=0.8)

# Customization
ax.set_ylabel('Percentage')
ax.set_title('Percentage of Each Category to Max 100%')
plt.savefig('testing.png')
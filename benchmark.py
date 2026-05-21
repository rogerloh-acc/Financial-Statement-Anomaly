import pandas as pd
import numpy as np
import time

# Generate dummy data
n = 100000
df = pd.DataFrame({
    'receivables_growth': np.random.randn(n),
    'rev_growth': np.random.randn(n),
    'inventory_growth': np.random.randn(n),
    'net_income': np.random.randn(n),
    'operating_cash_flow': np.random.randn(n),
    'ocf_to_net_income': np.random.randn(n),
    'gross_margin_change': np.random.randn(n),
    'ocf_growth': np.random.randn(n),
    'debt_growth': np.random.randn(n),
    'current_ratio': np.random.randn(n),
    'accruals_ratio': np.random.randn(n),
    'beneish_flag': np.random.choice([True, False], n)
})

df1 = df.copy()
df2 = df.copy()

# Old approach
def assign_anomaly_score(row):
    score = 0
    flags = []
    if row['receivables_growth'] - row['rev_growth'] > 0.20:
        score += 1
        flags.append("Rec > Rev Growth")
    if row['inventory_growth'] - row['rev_growth'] > 0.20:
        score += 1
        flags.append("Inv > Rev Growth")
    if row['net_income'] > 0 and row['operating_cash_flow'] < 0:
        score += 2
        flags.append("Positive NI, Negative OCF")
    if row['ocf_to_net_income'] < 0.5:
        score += 1
        flags.append("Weak OCF/NI")
    if row['gross_margin_change'] < -0.10:
        score += 1
        flags.append("Sharp GM Drop")
    if row['rev_growth'] > 0.15 and row['ocf_growth'] < -0.10:
        score += 2
        flags.append("Rev Growth vs OCF Drop")
    if row['debt_growth'] > 0.50:
        score += 1
        flags.append("Debt Spike")
    if row['current_ratio'] < 1.0:
        score += 1
        flags.append("Current Ratio < 1")
    if row['accruals_ratio'] > 0.10:
        score += 1
        flags.append("High Accruals")
    if row['beneish_flag']:
        score += 2
        flags.append("Beneish M-Score > -2.22")
    return score, ", ".join(flags)

def assign_risk_level(score):
    if score >= 4: return 'High'
    elif score >= 2: return 'Medium'
    else: return 'Low'

start = time.time()
df1['anomaly_score'], df1['key_red_flags'] = zip(*df1.apply(assign_anomaly_score, axis=1))
df1['anomaly_risk_level'] = df1['anomaly_score'].apply(assign_risk_level)
end1 = time.time() - start

# New approach
start = time.time()
conditions = [
    (df2['receivables_growth'] - df2['rev_growth'] > 0.20, 1, "Rec > Rev Growth"),
    (df2['inventory_growth'] - df2['rev_growth'] > 0.20, 1, "Inv > Rev Growth"),
    ((df2['net_income'] > 0) & (df2['operating_cash_flow'] < 0), 2, "Positive NI, Negative OCF"),
    (df2['ocf_to_net_income'] < 0.5, 1, "Weak OCF/NI"),
    (df2['gross_margin_change'] < -0.10, 1, "Sharp GM Drop"),
    ((df2['rev_growth'] > 0.15) & (df2['ocf_growth'] < -0.10), 2, "Rev Growth vs OCF Drop"),
    (df2['debt_growth'] > 0.50, 1, "Debt Spike"),
    (df2['current_ratio'] < 1.0, 1, "Current Ratio < 1"),
    (df2['accruals_ratio'] > 0.10, 1, "High Accruals"),
    (df2['beneish_flag'], 2, "Beneish M-Score > -2.22")
]

score = np.zeros(len(df2), dtype=int)
flags = np.full(len(df2), '', dtype=object)

for cond, points, msg in conditions:
    score += np.where(cond, points, 0)
    # Add comma if not empty
    prefix = np.where(flags == '', '', ', ')
    flags = np.where(cond, flags + prefix + msg, flags)

df2['anomaly_score'] = score
df2['key_red_flags'] = flags
df2['anomaly_risk_level'] = np.select(
    [df2['anomaly_score'] >= 4, df2['anomaly_score'] >= 2],
    ['High', 'Medium'],
    default='Low'
)
end2 = time.time() - start

print(f"Old time: {end1:.4f}s")
print(f"New time: {end2:.4f}s")
print(f"Speedup: {end1/end2:.2f}x")

# Check if outputs match
assert (df1['anomaly_score'] == df2['anomaly_score']).all()
assert (df1['key_red_flags'] == df2['key_red_flags']).all()
assert (df1['anomaly_risk_level'] == df2['anomaly_risk_level']).all()
print("Outputs match!")

import json
import subprocess
import pandas as pd
from datetime import datetime

def run_sc_command(subcommand_args):
    """Helper to run scalable-cli via Podman and return parsed JSON."""
    cmd = [
        "podman", "run", "--rm",
        "-v", "scalable-config:/root/.config/scalable-cli",
        "scalable-cli:latest"
    ] + subcommand_args + ["--json"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

print("Fetching portfolio holdings...")
holdings_res = run_sc_command(["broker", "holdings"])
positions = holdings_res.get('data', {}).get('result', {}).get('items', [])

print("Fetching portfolio overview (performance timeframes)...")
overview_res = run_sc_command(["broker", "overview"])
perf_list = overview_res.get('data', {}).get('result', {}).get('performance', [])
overview_data = {}
for p in perf_list:
    tf = p.get('timeframe')
    if tf:
        overview_data[tf] = {
            'absolute': p.get('simpleAbsoluteReturn', 0),
            'percentage': p.get('simplePercentageReturn', 0)
        }

print("Fetching all transactions with pagination (page-size 100)...")
all_transactions = []
cursor = None

while True:
    args = ["broker", "transactions", "--page-size", "100"]
    if cursor:
        args.extend(["--cursor", cursor])
        
    tx_res = run_sc_command(args)
    result_data = tx_res.get('data', {}).get('result', {})
    
    items = result_data.get('items', [])
    all_transactions.extend(items)
    
    # Check for next pagination cursor
    cursor = result_data.get('cursor') or result_data.get('next_cursor')
    if not items or not cursor:
        break

print(f"Total transactions fetched: {len(all_transactions)}")

records = []

for pos in positions:
    isin = pos.get('isin')
    name = pos.get('name', isin)
    qty = float(pos.get('quantity', 0))
    current_val = float(pos.get('valuation', 0))
    
    fifo_price = float(pos.get('fifo_price', 0))
    cost_basis = qty * fifo_price

    # Filter transactions for this specific ISIN
    pos_txs = [t for t in all_transactions if t.get('related_isin') == isin]
    
    # 1. Period calculation from first transaction date
    tx_dates = []
    for t in pos_txs:
        date_str = t.get('last_event_datetime')
        if date_str:
            try:
                tx_dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
            except ValueError:
                pass
                
    if tx_dates:
        first_tx = min(tx_dates)
        days_held = (datetime.now(first_tx.tzinfo) - first_tx).days
        period_str = f"{first_tx.strftime('%Y-%m-%d')} ({days_held}d)"
    else:
        period_str = "N/A"

    # 2. Return calculations
    total_return = current_val - cost_basis
    return_pct = (total_return / cost_basis * 100) if cost_basis > 0 else 0.0

    # 3. Distributions & Yields
    div_txs = [t for t in pos_txs if t.get('cash_transaction_type') == 'DISTRIBUTION']
    total_dist = sum(float(t.get('amount', 0)) for t in div_txs)
    
    dist_pct_sum = 0.0
    for div in div_txs:
        div_amount = float(div.get('amount', 0))
        val_at_dist = float(div.get('valuation_at_time', current_val))
        if val_at_dist > 0:
            dist_pct_sum += (div_amount / val_at_dist) * 100

    total_combined = total_return + total_dist

    records.append({
        'Share/ETF': name,
        'Period': period_str,
        'NumberOfShare': qty,
        'CurrentValue': round(current_val, 2),
        'TotalReturn': round(total_return, 2),
        'ReturnPercentage': f"{return_pct:.2f}%",
        'TotalDistribution': round(total_dist, 2),
        'DistributionPercentage': f"{dist_pct_sum:.2f}%",
        'Total(Return + Distribution)': round(total_combined, 2)
    })

# Output holdings table
df = pd.DataFrame(records)
print("\n--- HOLDINGS OVERVIEW ---")
print(df.to_string(index=False))
df.to_csv('portfolio_overview.csv', index=False)
print("Saved report to portfolio_overview.csv")

# Output Portfolio-Level Timeframe Performance (YTD, MAX, etc.)
if overview_data:
    print("\n--- PORTFOLIO TIMEFRAME PERFORMANCE (overview) ---")
    perf_rows = []
    for tf in ['YTD', 'ONE_YEAR', 'THREE_MONTHS', 'SIX_MONTHS', 'ONE_MONTH', 'MAX']:
        if tf in overview_data:
            vals = overview_data[tf]
            perf_rows.append({
                'Timeframe': tf, 
                'Absolute Return': round(vals['absolute'], 2), 
                'Percentage Return': f"{vals['percentage']:.2f}%"
            })
    df_perf = pd.DataFrame(perf_rows)
    print(df_perf.to_string(index=False))
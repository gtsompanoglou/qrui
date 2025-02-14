from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load inventory
inventory_file = "priced_inventory.csv"
df = pd.read_csv(inventory_file)

# Add an 'order' column if it does not exist
df['order'] = df.get('order', pd.NA)

order_buffer = []  # Temporary storage for current order
current_order_number = 1  # Order counter
order_total_cost = 0.0  # Total cost of the current order

def save_inventory():
    df.to_csv(inventory_file, index=False)

def get_inventory_view():
    return df[df['order'].isna()].groupby(['type', 'color', 'size']).size().unstack(fill_value=0)

@app.route('/')
def index():
    inventory_view = get_inventory_view()
    inventory_sizes = list(inventory_view.columns) if not inventory_view.empty else []
    return render_template('index.html', inventory=inventory_view.to_dict(orient='index'), sizes=inventory_sizes, order_buffer=order_buffer, current_order_number=current_order_number, order_total_cost=order_total_cost)

@app.route('/scan', methods=['POST'])
def scan():
    global order_buffer, current_order_number, order_total_cost
    data = request.json
    pk = data.get('pk')
    
    item_info = df.loc[df['pk'] == pk, ['type', 'color', 'size', 'price']].values.tolist()
    if pk == "endorder":
        if order_buffer:
            df.loc[df['pk'].isin(order_buffer), 'order'] = current_order_number
            save_inventory()
            order_buffer = []  # Clear buffer
            order_total_cost = 0.0  # Reset total cost
            current_order_number += 1  # Increment order number
            return jsonify({"success": True, "order_size": len(order_buffer), "order_number": current_order_number - 1, "order_items": [], "order_total_cost": order_total_cost})
        else:
            return jsonify({"success": False, "message": "No items scanned for this order."}), 400
    
    if pk in df['pk'].values:
        order_buffer.append(pk)
        item_price = df.loc[df['pk'] == pk, 'price'].values[0]
        order_total_cost += item_price
        return jsonify({"success": True, "order_size": len(order_buffer), "order_number": current_order_number, "order_items": item_info, "order_total_cost": order_total_cost})
    else:
        return jsonify({"success": False, "message": "Item not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)

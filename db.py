# db.py の最新版
import sqlite3
import pandas as pd

DB_NAME = 'cost.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            pattern_id INTEGER,
            item_key TEXT,
            item_value TEXT,
            PRIMARY KEY (pattern_id, item_key)
        )
    ''')
    
    default_settings = {
        'ac_a4_cost': '500', 'ac_a3_cost': '1000', 'mdf_a4_cost': '300', 'mdf_a3_cost': '600',
        'ac_a4_sec': '300', 'ac_a3_sec': '600', 'mdf_a4_sec': '240', 'mdf_a3_sec': '480',
        'ac_a4_mac': '10', 'ac_a3_mac': '20', 'mdf_a4_mac': '10', 'mdf_a3_mac': '20',
        'profit_1': '10', 'profit_2': '40', 'profit_3': '70',
        'loss_1': '0', 'loss_2': '10', 'loss_3': '20',
        'ink_1': '10', 'ink_2': '30', 'ink_3': '50', 'ink_4': '80', 'ink_5': '120',
        'ink_mat_cost': '20', 'ink_mat_sec': '60',
        'ink_clr_cost': '20', 'ink_clr_sec': '60',
        'ink_wht_cost': '30', 'ink_wht_sec': '90',
    }
    
    for i in range(1, 11):
        default_settings[f'pack_{i}_name'] = f'梱包オプション{i}' if i == 1 else ''
        default_settings[f'pack_{i}_cost'] = '10' if i == 1 else '0'
        default_settings[f'pack_{i}_sec'] = '10' if i == 1 else '0'

    for p_id in range(1, 6):
        for key, val in default_settings.items():
            c.execute("INSERT OR IGNORE INTO settings (pattern_id, item_key, item_value) VALUES (?, ?, ?)",
                      (p_id, key, val))
    
    conn.commit()
    conn.close()

def get_settings(pattern_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT item_key, item_value FROM settings WHERE pattern_id = ?", (pattern_id,))
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_setting(pattern_id, item_key, new_value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE settings SET item_value = ? WHERE pattern_id = ? AND item_key = ?", 
              (str(new_value), pattern_id, item_key))
    conn.commit()
    conn.close()
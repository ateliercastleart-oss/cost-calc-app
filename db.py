# db.py
import sqlite3
import pandas as pd

DB_NAME = 'cost.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # マスタ設定テーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            pattern_id INTEGER,
            item_key TEXT,
            item_value TEXT,
            PRIMARY KEY (pattern_id, item_key)
        )
    ''')
    # 💡新規追加：案件の入力内容（Order1~10）を10セット保存するテーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_templates (
            template_id INTEGER PRIMARY KEY,
            template_name TEXT,
            template_data TEXT
        )
    ''')
    
    # パターン1〜5の初期データ
    default_settings = {
        'ac_a4_cost': '500', 'ac_a4_sec': '300', 'ac_a4_mac': '10',
        'ac_a3_cost': '1000', 'ac_a3_sec': '600', 'ac_a3_mac': '20',
        'mdf_a4_cost': '300', 'mdf_a4_sec': '240', 'mdf_a4_mac': '10',
        'mdf_a3_cost': '600', 'mdf_a3_sec': '480', 'mdf_a3_mac': '20',
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
            
    # 💡保存枠1〜10を初期化（まだデータがない状態）
    for t_id in range(1, 11):
        c.execute("INSERT OR IGNORE INTO order_templates (template_id, template_name, template_data) VALUES (?, ?, ?)",
                  (t_id, f"保存枠 {t_id} (未保存)", ""))
                  
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

# 💡新規追加：テンプレート枠一覧の取得
def get_order_templates():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT template_id, template_name FROM order_templates ORDER BY template_id ASC")
    rows = c.fetchall()
    conn.close()
    return rows

# 💡新規追加：現在の案件内容（JSON文字列）を保存
def save_order_template(template_id, name, data_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE order_templates SET template_name = ?, template_data = ? WHERE template_id = ?", 
              (name, data_str, template_id))
    conn.commit()
    conn.close()

# 💡新規追加：保存されたデータ文字列を読み込み
def load_order_template(template_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT template_data FROM order_templates WHERE template_id = ?", (template_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""
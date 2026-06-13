import streamlit as st
import db
import math
import pandas as pd
import datetime
import json

st.markdown("""
    <style>
    /* ダークモード/ライトモードを自動検知して色を変える */
    @media (prefers-color-scheme: dark) {
        :root { --text-color: #ffffff; --bg-color: #1e1e1e; }
        h1, h2, h3 { color: #d6a4ff; } /* 暗い背景で映える薄い紫 */
    }
    @media (prefers-color-scheme: light) {
        :root { --text-color: #333333; --bg-color: #fcf9ff; }
        h1, h2, h3 { color: #6a1b9a; } /* 明るい背景で映える濃い紫 */
    }
    .stApp { background-color: var(--bg-color); color: var(--text-color); }
    </style>
""", unsafe_allow_html=True)

# 起動時のデータベース初期化
db.init_db()

# --- UI設定：薄い紫のテーマカラーと全体デザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #fcf9ff; }
    div.stButton > button:first-child { background-color: #9b59b6; color: white; border: none; }
    div.stButton > button:first-child:hover { background-color: #8e44ad; color: white; }
    h1, h2, h3 { color: #6a1b9a; }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="原価計算・丁付け管理システム", layout="wide")

# インク使用量の選択肢マッピング
INK_DISPLAY_OPTS = ["なし", "レベル1（少）", "レベル2", "レベル3（中）", "レベル4", "レベル5（多）"]

# セッション管理（ページ切り替えしても数値を完全に保持する仕組み）
if 'order_data' not in st.session_state:
    st.session_state.order_data = {
        i: {
            'qty': 0, 'tori': 15, 'mat': "アクリル A4", 'ink': "なし",
            'mat_c': 0, 'clr_c': 0, 'wht_c': 0, 'packs': [], 
            'loss_opt': 1, 'prof_opt': 1
        } for i in range(1, 11)
    }

st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ移動", ["データ入力（マスタ設定）", "データ出力（原価計算）", "データまとめ", "とり（丁付け）確認"])

def get_num(d, key, default=0.0):
    try: return float(d.get(key, default))
    except (ValueError, TypeError): return float(default)

# 画面表示用の日本語時間フォーマット
def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h}時間{m}分{s}秒"

# 💡新規追加：CSV出力用の英語時間フォーマット
def format_time_en(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h}h {m}m {s}s"

def get_pattern_dict():
    p_names = {}
    for p in range(1, 6):
        s = db.get_settings(p)
        name = s.get('pattern_name', '')
        p_names[p] = name if name else f"パターン {p}"
    return p_names

# ==========================================
# ページ1：データ入力（マスタ設定）
# ==========================================
if page == "データ入力（マスタ設定）":
    st.title("⚙️ データ入力（マスタ設定）")
    
    p_names = get_pattern_dict()
    pattern_id = st.selectbox("📂 読み込む/保存する設定パターンを選択", [1, 2, 3, 4, 5], format_func=lambda x: f"{x}: {p_names[x]}")
    s = db.get_settings(pattern_id)
    
    def save_settings_ui(position=""):
        if st.form_submit_button(f"💾 「{p_names[pattern_id]}」に設定を保存する {position}"):
            for key in st.session_state.keys():
                if key.endswith(f"_p{pattern_id}"):
                    db.update_setting(pattern_id, key.replace(f"_p{pattern_id}", ""), st.session_state[key])
            st.success(f"「{st.session_state[f'pattern_name_p{pattern_id}']}」として設定を保存しました！")
            st.rerun()

    with st.form("settings_form"):
        st.text_input("📝 このパターンの名前（任意）", value=s.get('pattern_name', ''), key=f"pattern_name_p{pattern_id}", placeholder="例：基本設定、大口案件用 など")
        
        save_settings_ui("(上部)")
        tab1, tab2, tab3, tab4 = st.tabs(["① 素材・時間・機械代", "② インク設定", "③ 梱包・袋詰め", "④ 利益率・ロスト率"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### アクリル")
                st.number_input("A4 原価 (円)", value=get_num(s, 'ac_a4_cost'), key=f"ac_a4_cost_p{pattern_id}")
                st.number_input("A4 加工時間 (秒)", value=get_num(s, 'ac_a4_sec'), key=f"ac_a4_sec_p{pattern_id}")
                st.number_input("A4 機械代 (円)", value=get_num(s, 'ac_a4_mac'), key=f"ac_a4_mac_p{pattern_id}")
                st.divider()
                st.number_input("A3 原価 (円)", value=get_num(s, 'ac_a3_cost'), key=f"ac_a3_cost_p{pattern_id}")
                st.number_input("A3 加工時間 (秒)", value=get_num(s, 'ac_a3_sec'), key=f"ac_a3_sec_p{pattern_id}")
                st.number_input("A3 機械代 (円)", value=get_num(s, 'ac_a3_mac'), key=f"ac_a3_mac_p{pattern_id}")
            with c2:
                st.markdown("##### MDF")
                st.number_input("A4 原価 (円)", value=get_num(s, 'mdf_a4_cost'), key=f"mdf_a4_cost_p{pattern_id}")
                st.number_input("A4 加工時間 (秒)", value=get_num(s, 'mdf_a4_sec'), key=f"mdf_a4_sec_p{pattern_id}")
                st.number_input("A4 機械代 (円)", value=get_num(s, 'mdf_a4_mac'), key=f"mdf_a4_mac_p{pattern_id}")
                st.divider()
                st.number_input("A3 原価 (円)", value=get_num(s, 'mdf_a3_cost'), key=f"mdf_a3_cost_p{pattern_id}")
                st.number_input("A3 加工時間 (秒)", value=get_num(s, 'mdf_a3_sec'), key=f"mdf_a3_sec_p{pattern_id}")
                st.number_input("A3 機械代 (円)", value=get_num(s, 'mdf_a3_mac'), key=f"mdf_a3_mac_p{pattern_id}")

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 基本インク代（A4換算）")
                for i in range(1, 6): 
                    st.number_input(f"レベル{i}", value=get_num(s, f'ink_{i}'), key=f"ink_{i}_p{pattern_id}")
            with c2:
                st.markdown("##### 追加インク (1回あたり)")
                st.number_input("マット 追加原価 (円)", value=get_num(s, 'ink_mat_cost'), key=f"ink_mat_cost_p{pattern_id}")
                st.number_input("マット 追加時間 (秒)", value=get_num(s, 'ink_mat_sec'), key=f"ink_mat_sec_p{pattern_id}")
                st.number_input("透明追加 追加原価 (円)", value=get_num(s, 'ink_clr_cost'), key=f"ink_clr_cost_p{pattern_id}")
                st.number_input("透明追加 追加時間 (秒)", value=get_num(s, 'ink_clr_sec'), key=f"ink_clr_sec_p{pattern_id}")
                st.number_input("白追加 追加原価 (円)", value=get_num(s, 'ink_wht_cost'), key=f"ink_wht_cost_p{pattern_id}")
                st.number_input("白追加 追加時間 (秒)", value=get_num(s, 'ink_wht_sec'), key=f"ink_wht_sec_p{pattern_id}")

        with tab3:
            st.markdown("##### 梱包・袋詰め・アセンブリ (最大10項目)")
            for i in range(1, 11):
                pc1, pc2, pc3 = st.columns([2, 1, 1])
                pc1.text_input(f"項目名 {i}", value=s.get(f'pack_{i}_name', ''), key=f"pack_{i}_name_p{pattern_id}")
                pc2.number_input(f"コスト(円) {i}", value=get_num(s, f'pack_{i}_cost'), key=f"pack_{i}_cost_p{pattern_id}")
                pc3.number_input(f"時間(秒) {i}", value=get_num(s, f'pack_{i}_sec'), key=f"pack_{i}_sec_p{pattern_id}")

        with tab4:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 利益率設定 (%)")
                for i in range(1, 4): 
                    st.number_input(f"利益率 {i}", value=get_num(s, f'profit_{i}'), key=f"profit_{i}_p{pattern_id}")
            with c2:
                st.markdown("##### ロスト率設定 (%)")
                for i in range(1, 4): 
                    st.number_input(f"ロスト率 {i}", value=get_num(s, f'loss_{i}'), key=f"loss_{i}_p{pattern_id}")

        st.divider()
        save_settings_ui("(下部)")

# ==========================================
# ページ2：データ出力（原価計算）
# ==========================================
elif page == "データ出力（原価計算）":
    st.title("📊 データ出力（原価計算）")
    
    p_names = get_pattern_dict()
    calc_pattern = st.selectbox("📄 適用するマスタ設定パターン", [1, 2, 3, 4, 5], format_func=lambda x: f"{x}: {p_names[x]}")
    s = db.get_settings(calc_pattern)
    pack_opts = {f"{i}: {s.get(f'pack_{i}_name')}": i for i in range(1, 11) if s.get(f'pack_{i}_name')}

    tabs = st.tabs([f"Order {i}" for i in range(1, 11)])
    
    for idx, tab in enumerate(tabs):
        i = idx + 1
        with tab:
            st.subheader(f"Order {i}")
            d = st.session_state.order_data[i]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                d['qty'] = st.number_input("製造予定個数 (0の場合はまとめに表示されません)", min_value=0, value=d['qty'], key=f"qty_{i}")
                d['tori'] = st.number_input("1シート丁付け数", min_value=1, value=d['tori'], key=f"tori_{i}")
                d['mat'] = st.selectbox("素材・サイズ", ["アクリル A4", "アクリル A3", "MDF A4", "MDF A3"], index=["アクリル A4", "アクリル A3", "MDF A4", "MDF A3"].index(d['mat']), key=f"mat_{i}")
                
                if d['ink'] not in INK_DISPLAY_OPTS: d['ink'] = "なし"
                d['ink'] = st.selectbox("インク使用量", INK_DISPLAY_OPTS, index=INK_DISPLAY_OPTS.index(d['ink']), key=f"ink_{i}")
                
                d['mat_c'] = st.number_input("マット追加(回)", min_value=0, value=d['mat_c'], key=f"mat_c_{i}")
                d['clr_c'] = st.number_input("透明追加(回)", min_value=0, value=d['clr_c'], key=f"clr_c_{i}")
                d['wht_c'] = st.number_input("白追加(回)", min_value=0, value=d['wht_c'], key=f"wht_c_{i}")
                
                valid_packs = [p for p in d['packs'] if p in pack_opts.keys()]
                d['packs'] = st.multiselect("袋詰め・梱包（複数可）", list(pack_opts.keys()), default=valid_packs, key=f"packs_{i}")
                
                d['loss_opt'] = st.selectbox("ロスト率", [1, 2, 3], index=d['loss_opt']-1, format_func=lambda x: f"設定{x} ({get_num(s, f'loss_{x}')}%)", key=f"loss_{i}")
                d['prof_opt'] = st.selectbox("利益率", [1, 2, 3], index=d['prof_opt']-1, format_func=lambda x: f"設定{x} ({get_num(s, f'profit_{x}')}%)", key=f"prof_{i}")

            with c2:
                if d['ink'] == "なし":
                    ink_cost = 0
                else:
                    lvl_num = d['ink'].split("レベル")[1][0]
                    ink_cost = get_num(s, f"ink_{lvl_num}")

                ms_key = "ac_a4" if d['mat'] == "アクリル A4" else "ac_a3" if d['mat'] == "アクリル A3" else "mdf_a4" if d['mat'] == "MDF A4" else "mdf_a3"
                base_cost = get_num(s, f"{ms_key}_cost")
                base_sec = get_num(s, f"{ms_key}_sec")
                base_mac = get_num(s, f"{ms_key}_mac")

                ext_ink_cost = d['mat_c'] * get_num(s, 'ink_mat_cost') + d['clr_c'] * get_num(s, 'ink_clr_cost') + d['wht_c'] * get_num(s, 'ink_wht_cost')
                ext_ink_sec = d['mat_c'] * get_num(s, 'ink_mat_sec') + d['clr_c'] * get_num(s, 'ink_clr_sec') + d['wht_c'] * get_num(s, 'ink_wht_sec')
                
                if "A3" in d['mat']:
                    ink_cost *= 2; ext_ink_cost *= 2; ext_ink_sec *= 2
                
                sheet_cost = base_cost + base_mac + ink_cost + ext_ink_cost
                sheet_sec = base_sec + ext_ink_sec
                
                pack_cost_ea = sum([get_num(s, f"pack_{pack_opts[p]}_cost") for p in d['packs']])
                pack_sec_ea = sum([get_num(s, f"pack_{pack_opts[p]}_sec") for p in d['packs']])
                
                loss_rate = get_num(s, f"loss_{d['loss_opt']}")
                req_sheets = math.ceil((math.ceil(d['qty'] / d['tori']) if d['tori'] > 0 else 0) * (1 + loss_rate / 100))
                
                total_cost = (req_sheets * sheet_cost) + (d['qty'] * pack_cost_ea)
                total_sec = (req_sheets * sheet_sec) + (d['qty'] * pack_sec_ea)
                unit_cost = total_cost / d['qty'] if d['qty'] > 0 else 0
                
                prof_rate = get_num(s, f"profit_{d['prof_opt']}")
                unit_sale = unit_cost * (1 + prof_rate / 100)
                unit_profit = unit_sale - unit_cost
                total_sale = unit_sale * d['qty']
                total_profit = unit_profit * d['qty']

                d['req_sheets'] = req_sheets; d['unit_cost'] = unit_cost; d['unit_sale'] = unit_sale
                d['total_cost'] = total_cost; d['total_sale'] = total_sale; d['total_profit'] = total_profit; d['total_sec'] = total_sec

                st.markdown("### 📝 算出結果")
                st.write(f"**必要シート数:** {req_sheets} シート (ロスト率 {loss_rate}% 込み)")
                st.write(f"**製造予定時間:** {format_time(total_sec)}")
                st.success(f"**1個あたりの原価: {unit_cost:.2f} 円**")
                st.warning(f"**1個あたりの販売価格: {unit_sale:.2f} 円** (利益: {unit_profit:.2f} 円)")
                st.info(f"**総原価: {total_cost:.0f}円 / 総売上: {total_sale:.0f}円 / 総利益: {total_profit:.0f}円**")

# ==========================================
# ページ3：データまとめ
# ==========================================
elif page == "データまとめ":
    st.title("📋 データまとめ")
    
    st.subheader("💾 見積もりパターンの保存・読み込み (最大10セット)")
    templates = db.get_order_templates()
    template_options = [f"{t[0]}: {t[1]}" for t in templates]
    
    col_load, col_save = st.columns(2)
    with col_load:
        selected_load = st.selectbox("📥 読み込む保存枠を選択", template_options, key="load_tpl_sel")
        if st.button("パターンを読み込む"):
            t_id = int(selected_load.split(":")[0])
            data_str = db.load_order_template(t_id)
            if data_str:
                loaded_data = json.loads(data_str)
                st.session_state.order_data = {int(k): v for k, v in loaded_data.items()}
                st.success("保存データを読み込みました！")
                st.rerun()
            else:
                st.error("この枠にはまだ見積もりデータが保存されていません。")
                
    with col_save:
        selected_save = st.selectbox("💾 保存する枠を選択", template_options, key="save_tpl_sel")
        new_name = st.text_input("保存するパターンの名前を入力", value="見積もりデータ")
        if st.button("現在の入力中身を保存する"):
            t_id = int(selected_save.split(":")[0])
            data_str = json.dumps(st.session_state.order_data)
            db.save_order_template(t_id, new_name, data_str)
            st.success(f"枠 {t_id} に「{new_name}」として保存しました！")
            st.rerun()

    st.divider()

    valid_data = []
    for i in range(1, 11):
        d = st.session_state.order_data[i]
        if d['qty'] > 0:
            valid_data.append({
                "Order": f"Order {i}", "予定個数": d['qty'], "必要シート数": d['req_sheets'],
                "1個原価": round(d['unit_cost'], 2), "1個売価": round(d['unit_sale'], 2),
                "総原価": round(d['total_cost'], 0), "総売上": round(d['total_sale'], 0), "総利益": round(d['total_profit'], 0),
                "総時間": d['total_sec']
            })
    
    if not valid_data:
        st.warning("データ出力ページで製造個数を1以上入力してください。数量0のOrderは除外されます。")
    else:
        df = pd.DataFrame(valid_data)
        total_qty = df["予定個数"].sum()
        total_cost = df["総原価"].sum()
        total_sale = df["総売上"].sum()
        total_profit = df["総利益"].sum()
        total_sec = df["総時間"].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("全Order 総個数", f"{total_qty:,.0f} 個")
        c2.metric("総合計 原価", f"{total_cost:,.0f} 円")
        c3.metric("総合計 売上", f"{total_sale:,.0f} 円")
        c4.metric("総合計 利益", f"{total_profit:,.0f} 円")
        st.write(f"**全Order 総製造時間:** {format_time(total_sec)}")
        
        # --- 画面表示用データ（日本語） ---
        df_disp = df.copy(); df_disp["総時間"] = df_disp["総時間"].apply(format_time)
        df_disp.set_index("Order", inplace=True); df_disp_t = df_disp.T
        
        df_disp_t.insert(0, "総合計 (Grand Total)", "")
        df_disp_t.at["予定個数", "総合計 (Grand Total)"] = str(int(total_qty))
        df_disp_t.at["必要シート数", "総合計 (Grand Total)"] = str(int(df["必要シート数"].sum()))
        df_disp_t.at["1個原価", "総合計 (Grand Total)"] = "-"
        df_disp_t.at["1個売価", "総合計 (Grand Total)"] = "-"
        df_disp_t.at["総原価", "総合計 (Grand Total)"] = str(int(total_cost))
        df_disp_t.at["総売上", "総合計 (Grand Total)"] = str(int(total_sale))
        df_disp_t.at["総利益", "総合計 (Grand Total)"] = str(int(total_profit))
        df_disp_t.at["総時間", "総合計 (Grand Total)"] = format_time(total_sec)
        df_disp_t.reset_index(inplace=True); df_disp_t.rename(columns={"index": "項目"}, inplace=True)
        
        st.divider()
        st.write("▼ データまとめプレビュー（※ダウンロードされるCSVは文字化け防止のため完全に英語表記になります）")
        st.dataframe(df_disp_t, use_container_width=True)
        
        # 💡新規追加：CSVダウンロード用データ（完全英語化・ローマ字化）
        csv_mapping = {
            "予定個数": "Qty", "必要シート数": "Req_Sheets", 
            "1個原価": "Unit_Cost", "1個売価": "Unit_Price",
            "総原価": "Total_Cost", "総売上": "Total_Sales", 
            "総利益": "Total_Profit", "総時間": "Total_Time"
        }
        df_csv = df.copy()
        df_csv["総時間"] = df_csv["総時間"].apply(format_time_en)
        df_csv.rename(columns=csv_mapping, inplace=True)
        df_csv.set_index("Order", inplace=True)
        df_t = df_csv.T
        
        df_t.insert(0, "Grand_Total", "")
        df_t.at["Qty", "Grand_Total"] = str(int(total_qty))
        df_t.at["Req_Sheets", "Grand_Total"] = str(int(df["必要シート数"].sum()))
        df_t.at["Unit_Cost", "Grand_Total"] = "-"
        df_t.at["Unit_Price", "Grand_Total"] = "-"
        df_t.at["Total_Cost", "Grand_Total"] = str(int(total_cost))
        df_t.at["Total_Sales", "Grand_Total"] = str(int(total_sale))
        df_t.at["Total_Profit", "Grand_Total"] = str(int(total_profit))
        df_t.at["Total_Time", "Grand_Total"] = format_time_en(total_sec)
        
        df_t.reset_index(inplace=True); df_t.rename(columns={"index": "Item"}, inplace=True)
        
        # 日本語が一切含まれていないため、通常のutf-8でエンコード（どんな環境でも絶対文字化けしません）
        csv = df_t.to_csv(index=False, encoding='utf-8')
        st.download_button(label="📥 見積もりデータ(CSV/英語)をダウンロード", data=csv, file_name='cost_estimate.csv', mime='text/csv')

        st.divider()
        
        st.subheader("📑 見積書の作成（PDF保存）")
        st.info("💡 下の見積書枠内にある「この見積書だけを印刷・PDF保存」ボタンを押すと、周りのメニューを巻き込まずに綺麗にPDF化できます。")
        
        today_str = datetime.date.today().strftime('%Y年%m月%d日')
        
        html_text = f"""
        <div style="background-color: #eee; padding: 10px; text-align: center;">
            <button onclick="printInvoice()" style="background-color: #9b59b6; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;">🖨️ この見積書だけを印刷・PDF保存</button>
        </div>
        
        <div id="invoice-area" style="font-family: sans-serif; padding: 40px; max-width: 800px; margin: auto; background-color: white;">
            <h2 style="text-align: center; letter-spacing: 5px; color: #333; margin-bottom: 30px;">御見積書</h2>
            <p style="text-align: right; color: #333;">発行日: {today_str}</p>
            <p style="font-size: 1.2em; border-bottom: 1px solid #000; width: 50%; padding-bottom: 5px; color: #333;"><strong> 御中</strong></p>
            <p style="margin-top: 20px; color: #333;">下記の通り御見積申し上げます。</p>
            <h3 style="border-bottom: 3px double #000; padding-bottom: 5px; color: #333;">御見積合計金額: ￥{total_sale:,.0f} - (税抜)</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 30px; color: #333;">
                <tr style="background-color: #f2f2f2; border-top: 2px solid #000; border-bottom: 2px solid #000;">
                    <th style="padding: 10px; text-align: left;">品名 / 摘要</th>
                    <th style="padding: 10px; text-align: right;">数量</th>
                    <th style="padding: 10px; text-align: right;">単価</th>
                    <th style="padding: 10px; text-align: right;">金額</th>
                </tr>
        """
        for item in valid_data:
            html_text += f"""
                <tr style="border-bottom: 1px solid #ccc;">
                    <td style="padding: 10px;">{item['Order']}</td>
                    <td style="padding: 10px; text-align: right;">{item['予定個数']}</td>
                    <td style="padding: 10px; text-align: right;">￥{item['1個売価']:,.2f}</td>
                    <td style="padding: 10px; text-align: right;">￥{item['総売上']:,.0f}</td>
                </tr>
            """
        html_text += """
            </table>
            <div style="margin-top: 50px; text-align: right; font-size: 0.9em; color: #555;">
                ※本見積もりの有効期限は発行日より30日とさせていただきます。
            </div>
        </div>
        
        <script>
        function printInvoice() {
            var printContents = document.getElementById('invoice-area').innerHTML;
            var popupWin = window.open('', '_blank', 'width=900,height=800');
            popupWin.document.open();
            popupWin.document.write('<html><head><title>御見積書</title><style>body{font-family:sans-serif;padding:30px;} table{width:100%;border-collapse:collapse;margin-top:30px;} th,td{border-bottom:1px solid #ccc;padding:10px;} th{background-color:#f2f2f2;} @media print{button{display:none;}}</style></head><body onload="window.print();window.close()">' + printContents + '</body></html>');
            popupWin.document.close();
        }
        </script>
        """
        st.components.v1.html(html_text, height=750, scrolling=True)

    st.divider()
    if st.button("🗑️ 全Orderの入力データをクリアする"):
        st.session_state.order_data = {
            i: {
                'qty': 0, 'tori': 15, 'mat': "アクリル A4", 'ink': "なし",
                'mat_c': 0, 'clr_c': 0, 'wht_c': 0, 'packs': [], 
                'loss_opt': 1, 'prof_opt': 1
            } for i in range(1, 11)
        }
        st.success("クリアしました！")
        st.rerun()

# ==========================================
# ページ4：とり（丁付け）確認
# ==========================================
elif page == "とり（丁付け）確認":
    st.title("📐 とり（丁付け）確認")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ボード設定")
        board_preset = st.selectbox("ボードサイズ", ["A4 (200×287)", "A3 (410×287)", "カスタム"])
        if board_preset == "A4 (200×287)": board_w, board_h = 200, 287
        elif board_preset == "A3 (410×287)": board_w, board_h = 410, 287
        else:
            board_w = st.number_input("ボード横幅 (mm)", value=200)
            board_h = st.number_input("ボード縦幅 (mm)", value=287)
        edge_margin = st.number_input("フチの死に幅（端の余白 mm）", min_value=0.0, value=5.0)
    with col2:
        st.subheader("オブジェクト設定")
        obj_w = st.number_input("オブジェクト幅 (mm)", min_value=1.0, value=50.0)
        obj_h = st.number_input("オブジェクト高さ (mm)", min_value=1.0, value=50.0)
        gap = st.number_input("間隔 (mm)", min_value=0.0, value=4.0)

    def calc_layout(b_w, b_h, o_w, o_h, g, margin):
        use_w, use_h = b_w - (margin * 2), b_h - (margin * 2)
        if use_w <= 0 or use_h <= 0: return 0, 0, 0
        cols, rows = math.floor((use_w + g) / (o_w + g)), math.floor((use_h + g) / (o_h + g))
        return cols, rows, cols * rows

    norm_cols, norm_rows, norm_total = calc_layout(board_w, board_h, obj_w, obj_h, gap, edge_margin)
    rot_cols, rot_rows, rot_total = calc_layout(board_w, board_h, obj_h, obj_w, gap, edge_margin)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write("### 縦置き（通常）")
        st.write(f"横に **{norm_cols}** 個 × 縦に **{norm_rows}** 個")
        st.metric("合計配置数", f"{norm_total} 個")
    with c2:
        st.write("### 横置き（90度回転）")
        st.write(f"横に **{rot_cols}** 個 × 縦に **{rot_rows}** 個")
        st.metric("合計配置数", f"{rot_total} 個")
    st.info(f"💡 最適な配置: **{'横置き（回転）' if rot_total > norm_total else '縦置き（通常）'}**")
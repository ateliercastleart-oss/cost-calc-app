import streamlit as st
import db
import math
import pandas as pd
import datetime

# 起動時のデータベース初期化
db.init_db()

# --- UI設定：薄い紫のテーマカラーと全体デザイン ---
st.markdown("""
    <style>
    /* 全体の背景色を薄い紫に */
    .stApp { background-color: #fcf9ff; }
    /* プライマリーボタン（保存ボタン等）の色を紫に */
    div.stButton > button:first-child { background-color: #9b59b6; color: white; border: none; }
    div.stButton > button:first-child:hover { background-color: #8e44ad; color: white; }
    /* 見出しの色を濃い紫に */
    h1, h2, h3 { color: #6a1b9a; }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="原価計算・丁付け管理システム", layout="wide")

# --- セッション管理（ページ移動しても入力値を保持する仕組み） ---
if 'order_data' not in st.session_state:
    st.session_state.order_data = {
        i: {
            'qty': 0, 'tori': 15, 'mat': "アクリル A4", 'ink': "なし",
            'mat_c': 0, 'clr_c': 0, 'wht_c': 0, 'packs': [], 
            'loss_opt': 1, 'prof_opt': 1
        } for i in range(1, 11)
    }

# --- サイドバー ---
st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ移動", ["データ入力（マスタ設定）", "データ出力（原価計算）", "データまとめ", "とり（丁付け）確認"])

# --- ヘルパー関数 ---
def get_num(d, key, default=0.0):
    try: return float(d.get(key, default))
    except (ValueError, TypeError): return float(default)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}時間{m}分{s}秒"

# ==========================================
# ページ1：データ入力（マスタ設定）
# ==========================================
if page == "データ入力（マスタ設定）":
    st.title("⚙️ データ入力（マスタ設定）")
    
    # パターン選択
    pattern_id = st.selectbox("📂 読み込む/保存する設定パターンを選択", [1, 2, 3, 4, 5], format_func=lambda x: f"パターン {x}")
    s = db.get_settings(pattern_id)
    
    # 保存ボタンのUI（上下に配置するために関数化）
    def save_settings_ui(position=""):
        if st.form_submit_button(f"💾 パターン {pattern_id} に設定を保存する {position}"):
            for key in st.session_state.keys():
                # 現在のパターンのキー（例: _p1）がついているものだけをDBに保存
                if key.endswith(f"_p{pattern_id}"):
                    base_key = key.replace(f"_p{pattern_id}", "")
                    db.update_setting(pattern_id, base_key, st.session_state[key])
            st.success(f"パターン {pattern_id} の設定を保存しました！")

    with st.form("settings_form"):
        save_settings_ui("(上部)") # 上部の保存ボタン
        
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
                st.number_input("透明 追加原価 (円)", value=get_num(s, 'ink_clr_cost'), key=f"ink_clr_cost_p{pattern_id}")
                st.number_input("透明 追加時間 (秒)", value=get_num(s, 'ink_clr_sec'), key=f"ink_clr_sec_p{pattern_id}")
                st.number_input("白版 追加原価 (円)", value=get_num(s, 'ink_wht_cost'), key=f"ink_wht_cost_p{pattern_id}")
                st.number_input("白版 追加時間 (秒)", value=get_num(s, 'ink_wht_sec'), key=f"ink_wht_sec_p{pattern_id}")

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
        save_settings_ui("(下部)") # 下部の保存ボタン

# ==========================================
# ページ2：データ出力（原価計算）
# ==========================================
elif page == "データ出力（原価計算）":
    st.title("📊 データ出力（原価計算）")
    
    # 計算のベースにするマスタパターンを選択
    calc_pattern = st.selectbox("📄 適用するマスタ設定パターン", [1, 2, 3, 4, 5], format_func=lambda x: f"パターン {x} の設定で計算")
    s = db.get_settings(calc_pattern)
    
    # 梱包オプションの選択肢を作成（名前が設定されているものだけ）
    pack_opts = {f"{i}: {s.get(f'pack_{i}_name')}": i for i in range(1, 11) if s.get(f'pack_{i}_name')}

    tabs = st.tabs([f"Order {i}" for i in range(1, 11)])
    
    for idx, tab in enumerate(tabs):
        i = idx + 1
        with tab:
            st.subheader(f"Order {i}")
            # d はページをまたいでも保持される辞書
            d = st.session_state.order_data[i]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                d['qty'] = st.number_input("製造予定個数 (0の場合はまとめに表示されません)", min_value=0, value=d['qty'], key=f"qty_{i}")
                d['tori'] = st.number_input("1シート丁付け数", min_value=1, value=d['tori'], key=f"tori_{i}")
                d['mat'] = st.selectbox("素材・サイズ", ["アクリル A4", "アクリル A3", "MDF A4", "MDF A3"], index=["アクリル A4", "アクリル A3", "MDF A4", "MDF A3"].index(d['mat']), key=f"mat_{i}")
                
                # インクと追加オプション
                ink_options = ["なし", "1", "2", "3", "4", "5"]
                d['ink'] = st.selectbox("インク使用量", ink_options, index=ink_options.index(d['ink']), key=f"ink_{i}")
                d['mat_c'] = st.number_input("マット追加(回)", min_value=0, value=d['mat_c'], key=f"mat_c_{i}")
                d['clr_c'] = st.number_input("透明追加(回)", min_value=0, value=d['clr_c'], key=f"clr_c_{i}")
                d['wht_c'] = st.number_input("白版追加(回)", min_value=0, value=d['wht_c'], key=f"wht_c_{i}")
                
                # 梱包オプション（パターンの切り替え等で無効なキーが入るのを防ぐ）
                valid_packs = [p for p in d['packs'] if p in pack_opts.keys()]
                d['packs'] = st.multiselect("袋詰め・梱包（複数可）", list(pack_opts.keys()), default=valid_packs, key=f"packs_{i}")
                
                # 利益・ロスト率
                d['loss_opt'] = st.selectbox("ロスト率", [1, 2, 3], index=d['loss_opt']-1, format_func=lambda x: f"設定{x} ({get_num(s, f'loss_{x}')}%)", key=f"loss_{i}")
                d['prof_opt'] = st.selectbox("利益率", [1, 2, 3], index=d['prof_opt']-1, format_func=lambda x: f"設定{x} ({get_num(s, f'profit_{x}')}%)", key=f"prof_{i}")

            with c2:
                # --- 計算ロジック ---
                ms_key = "ac_a4" if d['mat'] == "アクリル A4" else "ac_a3" if d['mat'] == "アクリル A3" else "mdf_a4" if d['mat'] == "MDF A4" else "mdf_a3"
                base_cost = get_num(s, f"{ms_key}_cost")
                base_sec = get_num(s, f"{ms_key}_sec")
                base_mac = get_num(s, f"{ms_key}_mac")

                ink_cost = 0 if d['ink'] == "なし" else get_num(s, f"ink_{d['ink']}")
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

                # 計算結果を辞書に保存（まとめページで使うため）
                d['req_sheets'] = req_sheets
                d['unit_cost'] = unit_cost
                d['unit_sale'] = unit_sale
                d['total_cost'] = total_cost
                d['total_sale'] = total_sale
                d['total_profit'] = total_profit
                d['total_sec'] = total_sec

                st.markdown("### 📝 算出結果")
                st.write(f"**必要シート数:** {req_sheets} シート (ロスト率 {loss_rate}% 込み)")
                st.write(f"**製造予定時間:** {format_time(total_sec)}")
                st.success(f"**1個あたりの原価: {unit_cost:.2f} 円**")
                st.warning(f"**1個あたりの販売価格: {unit_sale:.2f} 円** (利益: {unit_profit:.2f} 円)")
                st.info(f"**総原価: {total_cost:.0f}円 / 総売上: {total_sale:.0f}円 / 総利益: {total_profit:.0f}円**")

# ==========================================
# ページ3：データまとめ・出力
# ==========================================
elif page == "データまとめ":
    st.title("📋 データまとめ")
    
    # qty(製造予定個数)が0より大きいOrderだけを抽出
    valid_data = []
    for i in range(1, 11):
        d = st.session_state.order_data[i]
        if d['qty'] > 0:
            valid_data.append({
                "Order": f"Order {i}",
                "予定個数": d['qty'],
                "必要シート数": d['req_sheets'],
                "1個原価": round(d['unit_cost'], 2),
                "1個売価": round(d['unit_sale'], 2),
                "総原価": round(d['total_cost'], 0),
                "総売上": round(d['total_sale'], 0),
                "総利益": round(d['total_profit'], 0),
                "総時間": d['total_sec']
            })
    
    if not valid_data:
        st.warning("データ出力ページで製造個数を1以上入力してください。（数量0のOrderは表示・出力されません）")
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
        
        # --- CSV出力用のデータ整形（縦横の入れ替え） ---
        df_csv = df.copy()
        df_csv["総時間"] = df_csv["総時間"].apply(format_time)
        df_csv.set_index("Order", inplace=True)
        df_t = df_csv.T # 転置
        
        # エラー修正：総計の数値を文字（文字列）に変換してから代入
        df_t.insert(0, "総合計 (Grand Total)", "")
        df_t.at["予定個数", "総合計 (Grand Total)"] = str(int(total_qty))
        df_t.at["必要シート数", "総合計 (Grand Total)"] = str(int(df["必要シート数"].sum()))
        df_t.at["1個原価", "総合計 (Grand Total)"] = "-"
        df_t.at["1個売価", "総合計 (Grand Total)"] = "-"
        df_t.at["総原価", "総合計 (Grand Total)"] = str(int(total_cost))
        df_t.at["総売上", "総合計 (Grand Total)"] = str(int(total_sale))
        df_t.at["総利益", "総合計 (Grand Total)"] = str(int(total_profit))
        df_t.at["総時間", "総合計 (Grand Total)"] = format_time(total_sec)

        df_t.reset_index(inplace=True)
        df_t.rename(columns={"index": "項目"}, inplace=True)
        
        st.divider()
        st.write("▼ CSV出力プレビュー")
        st.dataframe(df_t, use_container_width=True)
        
        # utf-8-sig でExcelの文字化け防止
        csv = df_t.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(label="📥 見積もりデータ(CSV)をダウンロード", data=csv, file_name='cost_estimate.csv', mime='text/csv')

        st.divider()
        
        # --- 見積書（PDF）作成機能 ---
        st.subheader("📑 見積書の作成（PDF保存）")
        st.info("💡 以下の枠内で **右クリック ➔ 「印刷」** （または Ctrl+P / Cmd+P）を押し、送信先を「PDFに保存」にすると綺麗な見積書が作成できます。")
        
        today_str = datetime.date.today().strftime('%Y年%m月%d日')
        
        html_text = f"""
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #ccc; max-width: 800px; margin: auto; background-color: white;">
            <h2 style="text-align: center; letter-spacing: 5px; color: #333;">御見積書</h2>
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
        """
        st.components.v1.html(html_text, height=600, scrolling=True)

    st.divider()
    if st.button("🗑️ 全Orderの入力データをクリアする"):
        # セッションの初期化（数量も0に戻す）
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
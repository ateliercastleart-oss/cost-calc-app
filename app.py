import streamlit as st
import db
import math
import pandas as pd

# 起動時のDB初期化
db.init_db()

st.set_page_config(page_title="原価計算・丁付け管理システム", layout="wide")

# 初期セッションステート（10ページ分の計算結果を保持）
if 'calc_results' not in st.session_state:
    st.session_state.calc_results = [{} for _ in range(10)]

# サイドバー
st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ移動", ["データ入力（マスタ設定）", "データ出力（原価計算）", "データまとめ", "とり（丁付け）確認"])

def get_num(d, key, default=0.0):
    try: return float(d.get(key, default))
    except ValueError: return float(default)

def format_time(seconds):
    """秒数を時間・分・秒に変換"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}時間{m}分{s}秒"

if page == "データ入力（マスタ設定）":
    st.title("⚙️ データ入力（マスタ設定）")
    pattern_id = st.selectbox("📂 読み込む/保存する設定パターンを選択", [1, 2, 3, 4, 5], format_func=lambda x: f"パターン {x}")
    s = db.get_settings(pattern_id)

    with st.form("settings_form"):
        tab1, tab2, tab3, tab4 = st.tabs(["① 素材・時間・機械代", "② インク設定", "③ 梱包・袋詰め", "④ 利益率・ロスト率"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### アクリル")
                st.number_input("A4 原価 (円)", value=get_num(s, 'ac_a4_cost'), key="ac_a4_cost")
                st.number_input("A4 加工時間 (秒)", value=get_num(s, 'ac_a4_sec'), key="ac_a4_sec")
                st.number_input("A4 機械代 (円)", value=get_num(s, 'ac_a4_mac'), key="ac_a4_mac")
                st.divider()
                st.number_input("A3 原価 (円)", value=get_num(s, 'ac_a3_cost'), key="ac_a3_cost")
                st.number_input("A3 加工時間 (秒)", value=get_num(s, 'ac_a3_sec'), key="ac_a3_sec")
                st.number_input("A3 機械代 (円)", value=get_num(s, 'ac_a3_mac'), key="ac_a3_mac")
            with c2:
                st.markdown("##### MDF")
                st.number_input("A4 原価 (円)", value=get_num(s, 'mdf_a4_cost'), key="mdf_a4_cost")
                st.number_input("A4 加工時間 (秒)", value=get_num(s, 'mdf_a4_sec'), key="mdf_a4_sec")
                st.number_input("A4 機械代 (円)", value=get_num(s, 'mdf_a4_mac'), key="mdf_a4_mac")
                st.divider()
                st.number_input("A3 原価 (円)", value=get_num(s, 'mdf_a3_cost'), key="mdf_a3_cost")
                st.number_input("A3 加工時間 (秒)", value=get_num(s, 'mdf_a3_sec'), key="mdf_a3_sec")
                st.number_input("A3 機械代 (円)", value=get_num(s, 'mdf_a3_mac'), key="mdf_a3_mac")

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 基本インク代（A4換算）")
                for i in range(1, 6):
                    st.number_input(f"レベル{i}", value=get_num(s, f'ink_{i}'), key=f"ink_{i}")
            with c2:
                st.markdown("##### 追加インク (1回あたり)")
                st.number_input("マット 追加原価 (円)", value=get_num(s, 'ink_mat_cost'), key="ink_mat_cost")
                st.number_input("マット 追加時間 (秒)", value=get_num(s, 'ink_mat_sec'), key="ink_mat_sec")
                st.number_input("透明 追加原価 (円)", value=get_num(s, 'ink_clr_cost'), key="ink_clr_cost")
                st.number_input("透明 追加時間 (秒)", value=get_num(s, 'ink_clr_sec'), key="ink_clr_sec")
                st.number_input("白版 追加原価 (円)", value=get_num(s, 'ink_wht_cost'), key="ink_wht_cost")
                st.number_input("白版 追加時間 (秒)", value=get_num(s, 'ink_wht_sec'), key="ink_wht_sec")

        with tab3:
            for i in range(1, 11):
                pc1, pc2, pc3 = st.columns([2, 1, 1])
                pc1.text_input(f"項目名 {i}", value=s.get(f'pack_{i}_name', ''), key=f"pack_{i}_name")
                pc2.number_input(f"コスト(円) {i}", value=get_num(s, f'pack_{i}_cost'), key=f"pack_{i}_cost")
                pc3.number_input(f"時間(秒) {i}", value=get_num(s, f'pack_{i}_sec'), key=f"pack_{i}_sec")

        with tab4:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 利益率設定 (%)")
                for i in range(1, 4): st.number_input(f"利益率 {i}", value=get_num(s, f'profit_{i}'), key=f"profit_{i}")
            with c2:
                st.markdown("##### ロスト率設定 (%)")
                for i in range(1, 4): st.number_input(f"ロスト率 {i}", value=get_num(s, f'loss_{i}'), key=f"loss_{i}")

        if st.form_submit_button(f"パターン {pattern_id} に設定を保存"):
            for key in st.session_state.keys():
                if key != f"FormSubmitter:settings_form-パターン {pattern_id} に設定を保存" and not key.startswith("FormSubmitter"):
                    db.update_setting(pattern_id, key, st.session_state[key])
            st.success("保存しました！")

elif page == "データ出力（原価計算）":
    st.title("📊 データ出力（原価計算）")
    # 計算の基準にするパターンを選択
    calc_pattern = st.selectbox("📄 適用するマスタ設定パターン", [1, 2, 3, 4, 5], format_func=lambda x: f"パターン {x} の設定で計算")
    s = db.get_settings(calc_pattern)
    
    # 梱包オプションのリスト作成
    pack_opts = {f"{i}: {s.get(f'pack_{i}_name')}": i for i in range(1, 11) if s.get(f'pack_{i}_name')}

    tabs = st.tabs([f"案件 {i}" for i in range(1, 11)])
    
    for idx, tab in enumerate(tabs):
        with tab:
            st.subheader(f"案件 {idx+1}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                qty = st.number_input("製造予定個数", min_value=0, value=100, key=f"qty_{idx}")
                tori = st.number_input("1シート丁付け数", min_value=1, value=15, key=f"tori_{idx}")
                
                mat_size = st.selectbox("素材・サイズ", ["アクリル A4", "アクリル A3", "MDF A4", "MDF A3"], key=f"mat_{idx}")
                ms_key = "ac_a4" if mat_size == "アクリル A4" else "ac_a3" if mat_size == "アクリル A3" else "mdf_a4" if mat_size == "MDF A4" else "mdf_a3"
                base_cost = get_num(s, f"{ms_key}_cost")
                base_sec = get_num(s, f"{ms_key}_sec")
                base_mac = get_num(s, f"{ms_key}_mac")

                ink_lvl = st.selectbox("インク使用量", ["なし", "1", "2", "3", "4", "5"], key=f"ink_{idx}")
                mat_cnt = st.number_input("マット追加(回)", 0, key=f"mat_c_{idx}")
                clr_cnt = st.number_input("透明追加(回)", 0, key=f"clr_c_{idx}")
                wht_cnt = st.number_input("白版追加(回)", 0, key=f"wht_c_{idx}")
                
                sel_packs = st.multiselect("袋詰め・梱包（複数可）", list(pack_opts.keys()), key=f"packs_{idx}")
                loss_opt = st.selectbox("ロスト率", [1, 2, 3], format_func=lambda x: f"設定{x} ({get_num(s, f'loss_{x}')}%)", key=f"loss_{idx}")
                prof_opt = st.selectbox("利益率", [1, 2, 3], format_func=lambda x: f"設定{x} ({get_num(s, f'profit_{x}')}%)", key=f"prof_{idx}")

            with c2:
                # ====== 計算ロジック ======
                # インク代
                ink_cost = 0 if ink_lvl == "なし" else get_num(s, f"ink_{ink_lvl}")
                ext_ink_cost = mat_cnt * get_num(s, 'ink_mat_cost') + clr_cnt * get_num(s, 'ink_clr_cost') + wht_cnt * get_num(s, 'ink_wht_cost')
                ext_ink_sec = mat_cnt * get_num(s, 'ink_mat_sec') + clr_cnt * get_num(s, 'ink_clr_sec') + wht_cnt * get_num(s, 'ink_wht_sec')
                
                # A3の場合はインク代と追加インク時間・コストを2倍
                if "A3" in mat_size:
                    ink_cost *= 2
                    ext_ink_cost *= 2
                    ext_ink_sec *= 2
                
                sheet_cost = base_cost + base_mac + ink_cost + ext_ink_cost
                sheet_sec = base_sec + ext_ink_sec
                
                # 梱包代（1個あたり）
                pack_cost_ea = sum([get_num(s, f"pack_{pack_opts[p]}_cost") for p in sel_packs])
                pack_sec_ea = sum([get_num(s, f"pack_{pack_opts[p]}_sec") for p in sel_packs])
                
                # ロスト率を加味した必要シート数
                loss_rate = get_num(s, f"loss_{loss_opt}")
                req_sheets_base = math.ceil(qty / tori) if tori > 0 else 0
                req_sheets = math.ceil(req_sheets_base * (1 + loss_rate / 100))
                
                # 総計
                total_mfg_cost = req_sheets * sheet_cost
                total_mfg_sec = req_sheets * sheet_sec
                total_pack_cost = qty * pack_cost_ea
                total_pack_sec = qty * pack_sec_ea
                
                total_cost = total_mfg_cost + total_pack_cost
                total_sec = total_mfg_sec + total_pack_sec
                
                unit_cost = total_cost / qty if qty > 0 else 0
                
                # 利益計算 (原価 × (1 + 利益率))
                prof_rate = get_num(s, f"profit_{prof_opt}")
                unit_sale = unit_cost * (1 + prof_rate / 100)
                unit_profit = unit_sale - unit_cost
                
                total_sale = unit_sale * qty
                total_profit = unit_profit * qty

                # 画面表示
                st.markdown("### 📝 算出結果")
                st.write(f"**必要シート数:** {req_sheets} シート (ロスト率 {loss_rate}% 込み)")
                st.write(f"**製造予定時間:** {format_time(total_sec)}")
                
                st.success(f"**1個あたりの原価: {unit_cost:.2f} 円**")
                st.warning(f"**1個あたりの販売価格: {unit_sale:.2f} 円** (利益: {unit_profit:.2f} 円)")
                st.info(f"**総原価: {total_cost:.0f}円 / 総売上: {total_sale:.0f}円 / 総利益: {total_profit:.0f}円**")
                
                # ステートに保存（まとめページ用）
                if qty > 0:
                    st.session_state.calc_results[idx] = {
                        "案件名": f"案件 {idx+1}", "予定個数": qty, "必要シート数": req_sheets,
                        "1個原価": round(unit_cost, 2), "1個売価": round(unit_sale, 2),
                        "総原価": round(total_cost, 0), "総売上": round(total_sale, 0), "総利益": round(total_profit, 0),
                        "総時間(秒)": total_sec
                    }
                else:
                    st.session_state.calc_results[idx] = {}

elif page == "データまとめ":
    st.title("📋 データまとめ")
    st.write("データ出力ページで入力した「案件1〜10」の合計を確認・出力できます。")

    # データが入っている案件だけ抽出
    valid_data = [d for d in st.session_state.calc_results if d]
    
    if not valid_data:
        st.warning("データ出力ページで数量を入力してください。")
    else:
        df = pd.DataFrame(valid_data)
        
        # 総合計の計算
        total_qty = df["予定個数"].sum()
        total_cost = df["総原価"].sum()
        total_sale = df["総売上"].sum()
        total_profit = df["総利益"].sum()
        total_sec = df["総時間(秒)"].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("全案件 総個数", f"{total_qty:,.0f} 個")
        c2.metric("総合計 原価", f"{total_cost:,.0f} 円")
        c3.metric("総合計 売上", f"{total_sale:,.0f} 円")
        c4.metric("総合計 利益", f"{total_profit:,.0f} 円")
        st.write(f"**全案件 総製造時間:** {format_time(total_sec)}")
        
        st.divider()
        # 表示用のデータフレーム（秒を文字列表示に）
        df_show = df.copy()
        df_show["総時間"] = df_show["総時間(秒)"].apply(format_time)
        df_show = df_show.drop(columns=["総時間(秒)"])
        st.dataframe(df_show, use_container_width=True)
        
        # CSV出力（Excel等で開けるようにcp932でエンコード）
        csv = df_show.to_csv(index=False, encoding='cp932')
        st.download_button(label="📥 見積もりデータ(CSV)をダウンロード", data=csv, file_name='cost_estimate.csv', mime='text/csv')

    st.divider()
    if st.button("🗑️ 全シートの入力データをクリア"):
        st.session_state.calc_results = [{} for _ in range(10)]
        st.success("クリアしました！データ出力ページの入力もリセットされます。")
        st.rerun()

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
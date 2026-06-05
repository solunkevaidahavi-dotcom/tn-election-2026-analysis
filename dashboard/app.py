import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="TN Election Analysis 2021-2026", layout="wide", page_icon="📊")

@st.cache_data
def load_and_process_data():
    try:
        df_21 = pd.read_csv('tn_2021_results.csv')
        df_26 = pd.read_csv('tn_2026_results.csv')
        master = pd.read_csv('constituency_master.csv')
    except FileNotFoundError:
        st.error("Please ensure all 3 CSV files are in the same folder.")
        return None, None, None, None, None

    # 1. Data Cleaning & Merging
    df_21['year'] = 2021
    df_26['year'] = 2026
    df = pd.concat([df_21, df_26], ignore_index=True)
    
    # Standardize columns
    df.columns = df.columns.str.strip()
    df['party'] = df['party'].str.strip().str.upper()
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0)

    main_parties = ['DMK', 'AIADMK', 'TVK']
    df['party_group'] = df['party'].apply(lambda x: x if x in main_parties else 'OTHERS')

    # Ensure 'region' exists. If not, merge with master using ac_number
    if 'region' not in df.columns:
        df = df.merge(master[['ac_number', 'region']], on='ac_number', how='left')

    df.dropna(subset=['region'], inplace=True)

    # 2. Determine Winners & Margins
    winners_idx = df.groupby(['ac_number', 'year'])['votes'].idxmax()
    winners = df.loc[winners_idx][['ac_number', 'year', 'party_group', 'constituency', 'region']].copy()
    winners.rename(columns={'party_group': 'winner'}, inplace=True)

    # Calculate margins
    df_sorted = df.sort_values(by=['ac_number', 'year', 'votes'], ascending=[True, True, False])
    margins = df_sorted.groupby(['ac_number', 'year'])['votes'].apply(lambda x: x.iloc[0] - x.iloc[1] if len(x) > 1 else x.iloc[0]).reset_index(name='margin')
    winners = winners.merge(margins, on=['ac_number', 'year'], how='left')

    # 3. Seat Distribution & Difference Calculation
    seat_counts = winners.groupby(['year', 'region', 'winner']).size().reset_index(name='seats')
    
    # Create a grid for all combinations (Years x Regions x Parties) to fill missing 0s
    all_regions = sorted(df['region'].unique())
    idx = pd.MultiIndex.from_product(
        [[2021, 2026], all_regions, main_parties], 
        names=['year', 'region', 'winner']
    )
    
    seat_counts = (seat_counts.set_index(['year', 'region', 'winner'])
                   .reindex(idx, fill_value=0)
                   .reset_index())
    
    # Filter to only major parties
    seat_counts = seat_counts[seat_counts['winner'].isin(main_parties)]

    # Pivot to compare 2021 vs 2026
    pivot_seats = seat_counts.pivot_table(
        index=['region', 'winner'], columns='year', values='seats', fill_value=0
    ).reset_index()
    pivot_seats.columns = ['Region', 'Party', 'Seats_2021', 'Seats_2026']
    
    # Calculate Gain/Loss
    pivot_seats['Change'] = pivot_seats['Seats_2026'] - pivot_seats['Seats_2021']
    
    # 4. Flip Analysis
    # Pivot winners to compare 2021 vs 2026 per constituency
    win_pivot = winners.pivot(index='ac_number', columns='year', values='winner').reset_index()
    win_pivot.columns = ['ac_number', 'winner_2021', 'winner_2026']
    win_pivot = win_pivot.merge(winners[['ac_number', 'constituency', 'region']].drop_duplicates('ac_number'), on='ac_number')
    
    # Identify Flips (Only major parties)
    mask = (win_pivot['winner_2021'] != win_pivot['winner_2026']) & \
           (win_pivot['winner_2021'].isin(main_parties)) & \
           (win_pivot['winner_2026'].isin(main_parties))
    flips = win_pivot[mask].copy()
    flips['flip_direction'] = flips['winner_2021'] + ' → ' + flips['winner_2026']

    # 5. Vote Share
    vote_sum = df.groupby(['year', 'region', 'party_group'])['votes'].sum().reset_index()
    region_sum = df.groupby(['year', 'region'])['votes'].sum().reset_index().rename(columns={'votes': 'total_region_votes'})
    vote_share = vote_sum.merge(region_sum, on=['year', 'region'])
    vote_share['vote_share_pct'] = (vote_share['votes'] / vote_share['total_region_votes']) * 100
    vote_share_main = vote_share[vote_share['party_group'].isin(main_parties)]

    return seat_counts, pivot_seats, flips, vote_share_main, win_pivot, winners

# Load Data
seat_counts, pivot_seats, flips, vote_share_main, win_pivot, winners = load_and_process_data()

if pivot_seats is None:
    st.stop()

# Dashboard Layout
st.title("📊 Tamil Nadu Election Analysis: 2021 vs 2026")
st.caption("Focus: DMK, AIADMK, TVK across 6 Standardized Regions")

# ========= TOP SUMMARY CARDS =========
total_flips = len(flips)

gains = pivot_seats[pivot_seats['Change'] > 0]
largest_gain = f"{gains.loc[gains['Change'].idxmax()]['Party']} (+{int(gains['Change'].max())})" if not gains.empty else "N/A"

losses = pivot_seats[pivot_seats['Change'] < 0]
largest_loss = f"{losses.loc[losses['Change'].idxmin()]['Party']} ({int(losses['Change'].min())})" if not losses.empty else "N/A"

region_changes = pivot_seats.groupby('Region')['Change'].apply(lambda x: x.abs().sum()).reset_index()
most_changed_region = region_changes.loc[region_changes['Change'].idxmax()]['Region'] if not region_changes.empty else "N/A"

st.markdown("---")
st.subheader("📌 Quick Headlines")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Total Flips", total_flips)
col_s2.metric("Largest Gain", largest_gain)
col_s3.metric("Largest Loss", largest_loss)
col_s4.metric("Most Changed Region", most_changed_region)

# ========= STORY INTRO (Step 1) =========
st.markdown("---")
st.subheader("🎬 Tonight's Show: 3 Simple Stories")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Story 1", "Which seats flipped?")
    st.caption("DMK ↔ AIADMK changes")

with col2:
    st.metric("Story 2", "TVK's impact?")
    st.caption("Where did new votes come from?")

with col3:
    st.metric("Story 3", "Urban vs Rural?")
    st.caption("Did cities vote differently?")

st.caption("💡 All data from Election Commission of India. No opinions. Just facts.")
st.markdown("---")

# ========= TABS WITH SIMPLE QUESTIONS (Step 2) =========
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️ Who won where?", 
    "🔄 Which seats flipped?", 
    "📊 Did vote share change?",
    "🌟 TVK Impact",
    "⚔️ Battlegrounds",
    "🤏 Closest Contests"
])

# ================= TAB 1: SEAT DISTRIBUTION =================
with tab1:
    st.subheader("Seat Distribution & Net Change by Region")
    
    # Grouped Bar Chart
    fig_seats = px.bar(seat_counts, x='region', y='seats', color='winner', barmode='group',
                       facet_col='year', facet_col_wrap=2,
                       category_orders={'winner': ['DMK', 'AIADMK', 'TVK']},
                       labels={'seats': 'Seats Won', 'region': 'Region', 'winner': 'Party'},
                       title="Seats Won Comparison (2021 vs 2026)")
    fig_seats.update_layout(
        legend_title="Party",
        font=dict(size=18, family="Arial"),
        title_font_size=22,
        margin=dict(l=30, r=30, t=50, b=30),
        hovermode='x unified'
    )
    st.plotly_chart(fig_seats, use_container_width=True)
    
    # ========= DYNAMIC ANCHOR SCRIPT FOR TAB 1 =========
    max_change = pivot_seats.loc[pivot_seats['Change'].abs().idxmax()]
    region_name = max_change['Region']
    party_name = max_change['Party']
    change_val = int(max_change['Change'])
    direction = "gained" if change_val > 0 else "lost"
    
    with st.expander("🎙️ Anchor Script for Story 1 (Click to expand)", expanded=False):
        st.markdown(f"""
        **Neutral, ready-to-read line:**  
        *"Across the 6 regions, seat counts shifted between 2021 and 2026. 
        The largest net change occurred in {region_name}, where {party_name} {direction} {abs(change_val)} seats."*
        
        *Source: Election Commission of India public data. No predictive or explanatory claims.*
        """)

    st.subheader("📉 Seat Gain/Loss Analysis (2026 vs 2021)")
    st.write("Positive values (🟢) indicate gains, negative values (🔴) indicate losses.")
    
    # Styling the DataFrame - FIXED: use .map() instead of deprecated .applymap()
    def color_change(val):
        if val > 0: return 'color: #008000; font-weight: bold'
        if val < 0: return 'color: #FF0000; font-weight: bold'
        return 'color: #666666'

    diff_table = pivot_seats[['Region', 'Party', 'Seats_2021', 'Seats_2026', 'Change']].copy()
    diff_table = diff_table.sort_values(['Region', 'Change'], ascending=[True, False])
    
    st.dataframe(
        diff_table.style.map(color_change, subset=['Change'])  # FIXED: .map() not .applymap()
                    .format({'Seats_2021': '{:.0f}', 'Seats_2026': '{:.0f}', 'Change': '{:+.0f}'}),
        use_container_width=True,
        hide_index=True
    )

# ================= TAB 2: FLIP STORY =================
with tab2:
    st.subheader("🔄 Constituency Flip Analysis (Major Parties)")
    st.metric("Total Major Party Flips", len(flips))
    
    col_flip1, col_flip2 = st.columns([2, 1])  # FIXED: renamed to avoid conflict with outer col1
    
    with col_flip1:
        # ========= SIMPLE REPLACEMENT FOR SANKEY =========
        if len(flips) > 0:
            flow_summary = flips.groupby(['winner_2021', 'winner_2026']).size().reset_index(name='count')
            flow_summary['flow'] = flow_summary['winner_2021'] + " → " + flow_summary['winner_2026']
            
            fig_flip_bar = px.bar(  # FIXED: renamed to fig_flip_bar to avoid collision
                flow_summary,
                x='flow',
                y='count',
                text='count',
                color='winner_2021',
                labels={'flow': 'Party Shift', 'count': 'Seats Flipped'},
                title="Seat Flips: 2021 → 2026"
            )
            fig_flip_bar.update_traces(textposition='outside')
            fig_flip_bar.update_layout(
                font=dict(size=18, family="Arial"),
                title_font_size=22,
                margin=dict(l=30, r=30, t=50, b=30),
                showlegend=False,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_flip_bar, use_container_width=True)
        else:
            st.info("No major party flips detected.")
        
        # ========= DYNAMIC ANCHOR SCRIPT FOR TAB 2 =========
        total_flips = len(flips)
        with st.expander("🎙️ Anchor Script for Story 2 (Click to expand)", expanded=False):
            st.markdown(f"""
            **Neutral, ready-to-read line:**  
            *"A total of {total_flips} constituencies changed hands between major parties. 
            These flips show where voter preferences shifted between 2021 and 2026."*
            
            *Source: Election Commission of India public data. No predictive or explanatory claims.*
            """)
    
    with col_flip2:
        st.markdown("### Flip Directions")
        flip_counts = flips['flip_direction'].value_counts().reset_index()
        flip_counts.columns = ['Flow', 'Count']
        fig_flip_summary = px.bar(flip_counts, x='Flow', y='Count', text='Count', title="Flip Count Summary")
        fig_flip_summary.update_layout(  # FIXED: added TV-friendly styling
            font=dict(size=18, family="Arial"),
            title_font_size=22,
            margin=dict(l=30, r=30, t=50, b=30),
            showlegend=False
        )
        st.plotly_chart(fig_flip_summary, use_container_width=True)

    st.subheader("📋 Detailed Flip List")
    st.dataframe(flips[['constituency', 'region', 'winner_2021', 'winner_2026']], use_container_width=True, hide_index=True)

# ================= TAB 3: VOTE SHARE =================
with tab3:
    st.subheader("📊 Vote Share % by Region")
    fig_votes = px.bar(vote_share_main, x='region', y='vote_share_pct', color='party_group', barmode='stack',
                       facet_col='year', facet_col_wrap=2,
                       category_orders={'party_group': ['DMK', 'AIADMK', 'TVK']},
                       labels={'vote_share_pct': 'Vote Share (%)', 'region': 'Region', 'party_group': 'Party'},
                       title="Vote Share % (2021 vs 2026)")
    fig_votes.update_yaxes(range=[0, 100])
    fig_votes.update_layout(
        legend_title="Party",
        font=dict(size=18, family="Arial"),
        title_font_size=22,
        margin=dict(l=30, r=30, t=50, b=30),
        hovermode='x unified'
    )
    st.plotly_chart(fig_votes, use_container_width=True)
    
    # ========= DYNAMIC ANCHOR SCRIPT FOR TAB 3 =========
    if not vote_share_main.empty:
        vote_pivot = vote_share_main.pivot_table(
            index=['region', 'party_group'], 
            columns='year', 
            values='vote_share_pct', 
            fill_value=0
        ).reset_index()
        vote_pivot['change'] = vote_pivot[2026] - vote_pivot[2021]
        max_vote_shift = vote_pivot.loc[vote_pivot['change'].abs().idxmax()]
        v_region = max_vote_shift['region']
        v_party = max_vote_shift['party_group']
        v_2021 = max_vote_shift[2021]
        v_2026 = max_vote_shift[2026]
    else:
        v_region, v_party, v_2021, v_2026 = "[Region]", "[Party]", "0", "0"
    
    with st.expander("🎙️ Anchor Script for Story 3 (Click to expand)", expanded=False):
        st.markdown(f"""
        **Neutral, ready-to-read line:**  
        *"In {v_region}, {v_party}'s vote share moved from {v_2021:.1f}% in 2021 to {v_2026:.1f}% in 2026. 
        These vote share shifts provide context for the seat changes shown earlier."*
        
        *Source: Election Commission of India public data. No predictive or explanatory claims.*
        """)

# ================= TAB 4: TVK IMPACT =================
with tab4:
    st.subheader("🌟 TVK Impact Analysis")
    tvk_seats = pivot_seats[(pivot_seats['Party'] == 'TVK')]
    tvk_total_seats = tvk_seats['Seats_2026'].sum() if not tvk_seats.empty else 0
    st.metric("Total Seats Won by TVK (2026)", int(tvk_total_seats))
    
    tvk_vs = vote_share_main[(vote_share_main['party_group'] == 'TVK') & (vote_share_main['year'] == 2026)]
    if not tvk_vs.empty:
        best_region_row = tvk_vs.loc[tvk_vs['vote_share_pct'].idxmax()]
        st.write(f"**Best Region for TVK (by Vote Share):** {best_region_row['region']} ({best_region_row['vote_share_pct']:.1f}%)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### TVK Seats by Region (2026)")
        if not tvk_seats.empty and tvk_total_seats > 0:
            fig_tvk_seats = px.pie(tvk_seats[tvk_seats['Seats_2026'] > 0], values='Seats_2026', names='Region', hole=0.4)
            st.plotly_chart(fig_tvk_seats, use_container_width=True)
        else:
            st.info("No seats won by TVK.")
            
    with col_t2:
        st.markdown("#### TVK Vote Share by Region (2026)")
        if not tvk_vs.empty:
            fig_tvk_vs = px.bar(tvk_vs, x='region', y='vote_share_pct', text='vote_share_pct', title="TVK Vote Share %")
            fig_tvk_vs.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_tvk_vs, use_container_width=True)
        else:
            st.info("No vote share data for TVK.")

# ================= TAB 5: BATTLEGROUNDS =================
with tab5:
    st.subheader("⚔️ Battleground Regions")
    if not flips.empty:
        flips_by_region = flips['region'].value_counts().reset_index()
        flips_by_region.columns = ['Region', 'Flips']
        top_flip_region = flips_by_region.iloc[0]
        
        swing_by_region = pivot_seats.groupby('Region')['Change'].apply(lambda x: x.abs().sum()).reset_index()
        top_swing_region = swing_by_region.loc[swing_by_region['Change'].idxmax()]
        
        col_b1, col_b2 = st.columns(2)
        col_b1.metric("Region with Most Flips", top_flip_region['Region'], f"{top_flip_region['Flips']} seats changed hands")
        col_b2.metric("Region with Biggest Seat Swing", top_swing_region['Region'], f"{int(top_swing_region['Change'])} total seat shift")
        
        st.markdown("#### Flips by Region")
        fig_b_flips = px.bar(flips_by_region, x='Region', y='Flips', text='Flips', color='Region')
        st.plotly_chart(fig_b_flips, use_container_width=True)
    else:
        st.info("No flips available to analyze.")

# ================= TAB 6: CLOSEST CONTESTS =================
with tab6:
    st.subheader("🤏 Closest Contests (2026)")
    winners_2026 = winners[winners['year'] == 2026].copy()
    if 'margin' in winners_2026.columns:
        closest = winners_2026.nsmallest(10, 'margin')[['constituency', 'region', 'winner', 'margin']]
        closest.index = range(1, len(closest) + 1)
        st.dataframe(closest.style.format({'margin': '{:,.0f}'}), use_container_width=True)
        
        fig_margin = px.bar(closest, x='margin', y='constituency', orientation='h', 
                            color='winner', text='margin', title="Top 10 Smallest Margins (2026)")
        fig_margin.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_margin, use_container_width=True)
    else:
        st.info("Margin data not available.")


# ========= NEUTRALITY FOOTER (Step 5) - MOVED TO END, OUTSIDE ALL TABS =========
st.markdown("---")
st.caption("🔒 Neutral & Fact-Based: All insights derived solely from Election Commission of India public data. No party symbols, leader images, predictive claims, or explanatory language used. This dashboard supports fact-based storytelling only.")
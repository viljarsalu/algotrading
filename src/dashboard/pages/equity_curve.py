"""
Equity Curve Dashboard - Streamlit App

Displays portfolio growth visualization with:
- Starting capital (baseline)
- Current portfolio value
- Growth/loss over time
- Key metrics and milestones
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="Equity Curve",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .profit {
        color: #28a745;
        font-weight: bold;
    }
    .loss {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def get_equity_curve_data(days: int = 30) -> Dict[str, Any]:
    """Fetch equity curve data from API."""
    try:
        # Get token from session state
        token = st.session_state.get("auth_token")
        if not token:
            st.error("Not authenticated. Please login first.")
            return None

        headers = {"Authorization": f"Bearer {token}"}
        
        # Fetch equity curve
        response = requests.get(
            f"http://localhost:8000/api/equity/curve?days={days}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch equity curve: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching equity curve: {str(e)}")
        return None


def get_equity_summary() -> Dict[str, Any]:
    """Fetch equity summary from API."""
    try:
        token = st.session_state.get("auth_token")
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            "http://localhost:8000/api/equity/summary",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching equity summary: {str(e)}")
        return None


def get_equity_milestones() -> Dict[str, Any]:
    """Fetch equity milestones from API."""
    try:
        token = st.session_state.get("auth_token")
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            "http://localhost:8000/api/equity/milestones",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching milestones: {str(e)}")
        return None


def create_equity_chart(curve_data: List[Dict]) -> go.Figure:
    """Create equity curve chart using Plotly."""
    
    df = pd.DataFrame(curve_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Get starting capital (first equity value)
    starting_capital = df['equity'].iloc[0] if len(df) > 0 else 0
    
    fig = go.Figure()
    
    # Add starting capital reference line
    fig.add_hline(
        y=starting_capital,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Starting Capital: ${starting_capital:,.2f}",
        annotation_position="right",
        name="Starting Capital"
    )
    
    # Add equity curve
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['equity'],
        mode='lines',
        name='Portfolio Value',
        line=dict(
            color='green' if df['equity'].iloc[-1] >= starting_capital else 'red',
            width=3
        ),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)' if df['equity'].iloc[-1] >= starting_capital else 'rgba(255, 0, 0, 0.1)',
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Portfolio Value:</b> $%{y:,.2f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Portfolio Equity Curve",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        ),
        yaxis=dict(
            tickformat='$,.0f'
        )
    )
    
    return fig


def create_growth_chart(curve_data: List[Dict]) -> go.Figure:
    """Create growth percentage chart."""
    
    df = pd.DataFrame(curve_data)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = go.Figure()
    
    # Add zero reference line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        name="Break Even"
    )
    
    # Add growth percentage line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['growth_percentage'],
        mode='lines+markers',
        name='Growth %',
        line=dict(
            color='green' if df['growth_percentage'].iloc[-1] >= 0 else 'red',
            width=2
        ),
        marker=dict(size=4),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Growth:</b> %{y:.2f}%<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Portfolio Growth Percentage",
        xaxis_title="Date",
        yaxis_title="Growth (%)",
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        yaxis=dict(
            tickformat='.2f',
            ticksuffix='%'
        )
    )
    
    return fig


def main():
    """Main Streamlit app."""
    
    st.title("📈 Equity Curve Dashboard")
    st.markdown("Track your portfolio growth from starting capital to current value")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        days = st.slider("Days to display", min_value=7, max_value=365, value=30, step=7)
        refresh_interval = st.selectbox(
            "Auto-refresh interval",
            ["Manual", "Every 5 seconds", "Every 30 seconds", "Every 1 minute"]
        )
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Fetch data
    with st.spinner("Loading equity curve data..."):
        curve_data = get_equity_curve_data(days)
        summary = get_equity_summary()
        milestones = get_equity_milestones()
    
    if not curve_data or not summary:
        st.error("Failed to load equity curve data. Please check your connection.")
        return
    
    # Key Metrics Row 1
    st.subheader("Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Starting Capital",
            f"${summary['starting_capital']:,.2f}",
            delta=None,
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "Current Equity",
            f"${summary['current_equity']:,.2f}",
            delta=f"${summary['growth_amount']:,.2f}",
            delta_color="normal" if summary['growth_amount'] >= 0 else "inverse"
        )
    
    with col3:
        growth_pct = summary['growth_percentage']
        st.metric(
            "Growth %",
            f"{growth_pct:.2f}%",
            delta=None,
            delta_color="off"
        )
    
    with col4:
        st.metric(
            "Max Drawdown",
            f"{summary['max_drawdown']:.2f}%",
            delta=None,
            delta_color="off"
        )
    
    # Equity Curve Chart
    st.subheader("Equity Curve")
    st.info(
        "🔵 **Blue dashed line** = Starting Capital | "
        "🟢 **Green line** = Portfolio Value (Profit) | "
        "🔴 **Red line** = Portfolio Value (Loss)"
    )
    
    equity_chart = create_equity_chart(curve_data['curve_data'])
    st.plotly_chart(equity_chart, use_container_width=True)
    
    # Growth Percentage Chart
    st.subheader("Growth Percentage Over Time")
    growth_chart = create_growth_chart(curve_data['curve_data'])
    st.plotly_chart(growth_chart, use_container_width=True)
    
    # Additional Metrics Row 2
    st.subheader("Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Peak Equity",
            f"${summary['max_equity']:,.2f}",
            delta=f"${summary['max_equity'] - summary['starting_capital']:,.2f}",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Realized PNL",
            f"${summary['total_realized_pnl']:,.2f}",
            delta=None,
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Unrealized PNL",
            f"${summary['total_unrealized_pnl']:,.2f}",
            delta=None,
            delta_color="off"
        )
    
    # Milestones Section
    if milestones:
        st.subheader("🎯 Growth Milestones")
        
        achieved = milestones.get('achieved_milestones', [])
        remaining = milestones.get('remaining_milestones', [])
        
        if achieved:
            st.success("✅ Achieved Milestones")
            for milestone in achieved:
                st.write(f"🏆 {milestone['label']} - Target: ${milestone['target']:,.2f}")
        
        if remaining:
            st.info("📍 Remaining Milestones")
            for milestone in remaining:
                progress = milestone['progress_percentage']
                st.progress(
                    min(progress / 100, 1.0),
                    text=f"{milestone['label']} - {progress:.1f}% complete (${milestone['remaining_amount']:,.2f} to go)"
                )
    
    # Data Table
    with st.expander("📊 View Raw Data"):
        df = pd.DataFrame(curve_data['curve_data'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df[['date', 'equity', 'pnl', 'growth_percentage']]
        df.columns = ['Date', 'Equity ($)', 'PNL ($)', 'Growth (%)']
        
        # Format numbers
        df['Equity ($)'] = df['Equity ($)'].apply(lambda x: f"${x:,.2f}")
        df['PNL ($)'] = df['PNL ($)'].apply(lambda x: f"${x:,.2f}")
        df['Growth (%)'] = df['Growth (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df, use_container_width=True)
    
    # Footer
    st.divider()
    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Data range: {days} days"
    )


if __name__ == "__main__":
    main()

if selected_module == "Revenue Analytics & Forecasting":
    st.header("📈 Revenue Analytics & Forecasting")
    st.write("Executive financial tracking, stream decomposition, and strategic long-term forecast models.")
    
    df_hist = load_historical_data()
    df_forecast = load_forecast_data()

    # 1. Historical Revenue Chart
    fig1 = render_historical_revenue_chart(
        df=df_hist,
        date_col="observation_date",
        revenue_col="total_revenue",
        monthly_target=2500000.0,
        unit_scale=1e6
    )
    if fig1:
        st.plotly_chart(fig1, use_container_width=True, config=get_executive_config())

    st.markdown("---")

    # 2. Revenue Breakdown Chart
    fig2 = render_revenue_breakdown_chart(
        df=df_hist,
        date_col="observation_date",
        trad_col="traditional_rev",
        nontrad_col="nontraditional_rev",
        unit_scale=1e6
    )
    if fig2:
        st.plotly_chart(fig2, use_container_width=True, config=get_executive_config())

    st.markdown("---")

    # 3. Forecast Chart
    milestones = {
        2028: "Phase I PAPs Online",
        2032: "Phase II Port Expansion",
        2036: "Full Logistics Integration"
    }
    
    fig3 = render_revenue_forecast_chart(
        df=df_forecast,
        year_col="fiscal_year",
        bau_col="bau_projection",
        masterplan_col="master_plan_val",
        unit_scale=1e6,
        milestones=milestones
    )
    if fig3:
        st.plotly_chart(fig3, use_container_width=True, config=get_executive_config())

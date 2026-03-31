with update_tab:
    current_accounts = accounts_df()
    if current_accounts.empty:
        st.info("Add accounts first before entering balances.")
    else:
        snapshot_date = st.date_input("Snapshot date", value=date.today(), key="snapshot_date")
        previous_snapshots = snapshots_df()

        if not previous_snapshots.empty:
            existing_for_date = previous_snapshots[previous_snapshots["Date"].dt.date == snapshot_date]
            latest_previous = (
                previous_snapshots
                .sort_values(by=["Date"])
                .drop_duplicates(subset=["Account Name", "Section"], keep="last")
            )
            previous_by_account = {
                (row["Account Name"], row["Section"]): row["Amount"]
                for _, row in latest_previous.iterrows()
            }
        else:
            existing_for_date = pd.DataFrame()
            previous_by_account = {}

        asset_accounts = current_accounts[current_accounts["Section"] == "Asset"].sort_values(
            by=["Type", "Account Name"]
        )
        liability_accounts = current_accounts[current_accounts["Section"] == "Liability"].sort_values(
            by=["Type", "Account Name"]
        )

        with st.form("snapshot_form"):
            balance_rows = []
            parse_errors = []
            asset_total = 0.0
            liability_total = 0.0

            def get_prefill(account, section):
                if not existing_for_date.empty and (
                    (existing_for_date["Account Name"] == account) &
                    (existing_for_date["Section"] == section)
                ).any():
                    return float(
                        existing_for_date.loc[
                            (existing_for_date["Account Name"] == account) &
                            (existing_for_date["Section"] == section),
                            "Amount",
                        ].iloc[0]
                    )
                elif (account, section) in previous_by_account:
                    return float(previous_by_account[(account, section)])
                return 0.0

            st.markdown("### Assets")
            if asset_accounts.empty:
                st.caption("No asset accounts added yet.")
            else:
                for _, row in asset_accounts.iterrows():
                    account = row["Account Name"]
                    section = row["Section"]
                    prefill = get_prefill(account, section)

                    cols = st.columns([2, 1])
                    cols[0].markdown(f"**{account}**  \n{row['Type']}")
                    amount_text = cols[1].text_input(
                        f"Amount for {account} {section}",
                        value=f"{prefill:,.2f}",
                        key=f"amount_{snapshot_date}_{section}_{account}",
                        label_visibility="collapsed",
                        help="You can type large values with commas, like 125,000.50",
                    )

                    try:
                        parsed_amount = parse_amount(amount_text)
                        asset_total += parsed_amount
                    except ValueError:
                        parsed_amount = None
                        parse_errors.append(account)

                    balance_rows.append(
                        {
                            "Date": pd.to_datetime(snapshot_date),
                            "Account Name": account,
                            "Section": row["Section"],
                            "Type": row["Type"],
                            "Amount": parsed_amount,
                        }
                    )

                st.caption(f"Asset subtotal: {format_currency(asset_total)}")

            st.divider()

            st.markdown("### Liabilities")
            if liability_accounts.empty:
                st.caption("No liability accounts added yet.")
            else:
                for _, row in liability_accounts.iterrows():
                    account = row["Account Name"]
                    section = row["Section"]
                    prefill = get_prefill(account, section)

                    cols = st.columns([2, 1])
                    cols[0].markdown(f"**{account}**  \n{row['Type']}")
                    amount_text = cols[1].text_input(
                        f"Amount for {account} {section}",
                        value=f"{prefill:,.2f}",
                        key=f"amount_{snapshot_date}_{section}_{account}",
                        label_visibility="collapsed",
                        help="Use positive numbers for liabilities.",
                    )

                    try:
                        parsed_amount = parse_amount(amount_text)
                        liability_total += parsed_amount
                    except ValueError:
                        parsed_amount = None
                        parse_errors.append(account)

                    balance_rows.append(
                        {
                            "Date": pd.to_datetime(snapshot_date),
                            "Account Name": account,
                            "Section": row["Section"],
                            "Type": row["Type"],
                            "Amount": parsed_amount,
                        }
                    )

                st.caption(f"Liability subtotal: {format_currency(liability_total)}")

            st.divider()
            st.markdown(f"**Estimated Net Worth:** {format_currency(asset_total - liability_total)}")

            save_snapshot = st.form_submit_button("Save full snapshot")
            if save_snapshot:
                if parse_errors:
                    st.error("Please fix the amount format for: " + ", ".join(parse_errors))
                else:
                    st.session_state.snapshots = [
                        s for s in st.session_state.snapshots
                        if pd.to_datetime(s["Date"]).date() != snapshot_date
                    ]
                    st.session_state.snapshots.extend(balance_rows)
                    st.success("Snapshot saved for all accounts on that date.")

        if not existing_for_date.empty:
            st.caption("A snapshot already existed for this date. Saving will replace it.")

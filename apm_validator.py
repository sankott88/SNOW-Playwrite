def validate_apm_id(context, apm_value):
    helper_page = context.new_page()

    URL = (
        f"https://URL.service-now.com/cmdb_ci_business_app_list.do"
        f"?sysparm_query=portfolio.nameSTARTSWITHconsulting^u_numberSTARTSWITH{apm_value}"
        f"&sysparm_view=business_applications&sysparm_list_header_search=true"
    )

    helper_page.goto("about:blank")
    helper_page.goto(URL, wait_until="domcontentloaded")

    # --- LOGIN (only if needed) ---
    try:
        helper_page.fill("input[type='email']", "EMAIL")
        helper_page.click("#idSIButton9")
        helper_page.fill("input[type='password']", "PW")
        helper_page.click("#idSIButton9")
    except:
        pass

    # --- HANDLE POPUPS ---
    for selector in ["#onetrust-accept-btn-handler", "button[aria-label='Close']"]:
        try:
            helper_page.locator(selector).click(timeout=3000)
        except:
            pass

    # ---  Decide root (iframe OR main page) ---
    root = helper_page

    if "now/nav/ui/classic" in helper_page.url:
        print("Classic UI detected → using iframe")
        helper_page.wait_for_selector('iframe[name="gsft_main"]', timeout=10000)
        root = helper_page.frame_locator('iframe[name="gsft_main"]').first
    else:
        print("Direct UI detected → using main page")

    # --- SEARCH (already filtered via URL, so just wait) ---
    row = root.locator("tbody.list2_body tr.list_row").first
    row.wait_for(timeout=30000)

    # --- EXTRACT ---
    business_unit_value = root.locator(
        "tbody.list2_body tr.list_row td:nth-child(6) > a"
    ).first.text_content()

    business_unit_value = business_unit_value.strip() if business_unit_value else ""

    print(f"Found business group value is: {business_unit_value}")

    allowed_values = {
        "Cyber",
        "Finance Transformation",
        "Regulatory Risk & Forensic",
        "National Consulting Services",
    }

    return "Yes" if business_unit_value in allowed_values else "No"

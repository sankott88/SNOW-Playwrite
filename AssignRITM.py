from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("URL_HERE", wait_until="networkidle")
    page.wait_for_load_state("domcontentloaded")       
    
    page.fill("input[type='email']","EMAIL_HERE")
    page.click("#idSIButton9")
    page.fill("input[type='password']","PWD_HERE")
    page.click('#idSIButton9')
    
    frame = page.frame_locator("#gsft_main")    
    frame.locator("a[aria-label*='Cookie Complance | Daily Operations']").click()

    page.wait_for_selector("iframe#gsft_main", timeout=60000)    
    
    # Wait for page navigation/network
    page.wait_for_load_state("networkidle")
    
    # Switch to ServiceNow main frame
    frame = page.frame(name="gsft_main")
    
    # Extra safety: ensure frame itself is loaded
    frame.wait_for_load_state()
    
    page.wait_for_load_state("networkidle")     
    result = frame.evaluate("""
    () => {
    function parseNum(t) {
        return parseInt(t.replace(/,/g,''), 10);
    }    
    for (const row of document.querySelectorAll("tr")) {
        const caption = row.querySelector("td.pivot_caption.pivot_left");
        if (!caption) continue;    
        if (caption.textContent.trim() !== "(empty)") continue;    
        // OPEN column = first pivot_cell with a link
        const openCell = row.querySelector("td.pivot_cell a[onclick*='generateDataPointClickUrl']");
        if (!openCell) continue;    
        const count = parseNum(openCell.textContent.trim());
        if (count > 0) {
        openCell.click();
        return { status: "CLICKED", count };
        }
    }    
    return { status: "NO_EMPTY_OPEN_RITM" };
    }
    """)
           
    if result["status"] == "NO_EMPTY_OPEN_RITM":
        print("No empty & open RITMs found")
    else:
        print(f"Total empty & open RITMs: {result['count']}")
    
    # Close OneTrust cookie banner if it appears
    try:
        page.locator("#onetrust-accept-btn-handler").click(timeout=5000)        
    except:
        pass

    # or alternative dismiss button
    try:
        page.locator("button[aria-label='Close']").click(timeout=5000)
    except:
        pass

    frame = page.frame(name="gsft_main") 
    ritm_links = frame.locator("a.linked.formlink")
    total_ritms = ritm_links.count()        
    print(f"Total RITMs on page: {total_ritms}")
    
    VALID_PORTFOLIOS = [
    "PORTFOLIOS_HERE"
    ]    

    initial_total_ritms = total_ritms
    Assigned_RITMs =0
    Open_RITM =0
    current_index = 0
    counter = total_ritms
 
    while current_index < total_ritms:    
        ritm = ritm_links.nth(current_index)
        ritm_text = ritm.inner_text()    
        print(f"\n Clicking RITM [{current_index + 1}]: {ritm_text}")
        ritm.click()    
        # Wait for RITM form to load
        frame.locator("span.tab_caption_text >> text=Variables").wait_for(timeout=15000)    
        # --- READ PORTFOLIO ---
        portfolio_value = frame.locator(
            "//label[.//span[normalize-space()='Portfolio']]"
        ).locator(
            "xpath=ancestor::div[contains(@class,'sc_variable_editor')]//input[starts-with(@id,'display_hidden.')]"
        ).input_value()        
        print(f" Portfolio value: {portfolio_value}")    
        portfolio_matched = portfolio_value in VALID_PORTFOLIOS
        if portfolio_matched:
            print("Portfolio matched → assigning")                                            
            
            # --- BACK (reliable) ---            
            page.evaluate("window.history.back()") 
            frame.locator("a.linked.formlink").first.wait_for(timeout=15000)

            # Right-click first RITM
            # RIGHT-CLICK SAME RITM
            ritm = frame.locator("a.linked.formlink").nth(current_index)
            ritm.click(button="right")       
            
            # Scope to the VISIBLE context menu only
            context_menu = frame.locator("div.context_menu:visible")
            
            # Click ONLY "Assign to me"
            assign_to_me = context_menu.locator(
                "div.context_item", has_text="Assign to me"
            )            
            assign_to_me.wait_for(state="visible", timeout=10000)
            assign_to_me.click()                        
           
            print("RITM Assigned to NAME matched → moving to next RITM") 
            
            # RESET index to FIRST RITM
            current_index = 0
            ritm_links = frame.locator("a.linked.formlink")            
            if counter == 0:
                break
            counter -=1
            Assigned_RITMs +=1
            continue
    
        else:            
            print("Portfolio NOT matched → moving to next RITM") 
            page.evaluate("window.history.back()")
            frame = page.frame(name="gsft_main")  
            frame.locator("a.linked.formlink").first.wait_for(timeout=15000) 
            if counter == 0:
                break
            counter -=1
            Open_RITM +=1
            current_index += 1            
            ritm_links = frame.locator("a.linked.formlink")

    print(f"\nAssignment completed Sucessfully. \n Total Initial Open RITM {initial_total_ritms} \n Assigned RITM count {Assigned_RITMs} \n Remaining Open RITM count {Open_RITM}")
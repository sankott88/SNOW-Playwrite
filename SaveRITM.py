from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://service-now.com/", wait_until="networkidle")
    page.wait_for_load_state("domcontentloaded")       
    
    page.fill("input[type='email']","EMAIL_ID")
    page.click("#idSIButton9")
    page.fill("input[type='password']","PASSWORD")
    page.click('#idSIButton9')
    
    frame = page.frame_locator("#gsft_main")
    frame.locator("a[aria-label*='SNOW widget']").click()
    frame.locator("span.list_group", has_text="TEXT_NAME").click()        
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

    while True:
        # ---------------------------
        # WAIT FOR LIST PAGE
        # ---------------------------
        page.wait_for_selector("#gsft_main", timeout=90000)
        frame = page.frame(name="gsft_main")

        # Wait until table + RITM links appear
        frame.wait_for_selector("table.list_table", timeout=90000)
        frame.wait_for_selector("a.linked.formlink", timeout=90000)

        # Select first RITM
        ritm_item = frame.locator("a.linked.formlink").first 
        if ritm_item.count() == 0:
            print("No more RITMs done.")
            break
    
        ritm_item.click()
    
        # ---------------------------
        # WAIT FOR RECORD PAGE
        # ---------------------------

        page.wait_for_load_state("domcontentloaded")
        frame = page.frame(name="gsft_main")
        frame.wait_for_selector("#sysverb_insert_and_stay", timeout=90000)

        #--------------------------------
        # SELECT THE COOKIE CONSENT COMPLIANT 'NO'
        #--------------------------------
        label = "Cookie Consent Compliant?"
    
        frame.evaluate("""
        (labelText) => {
        const spans = Array.from(document.querySelectorAll('span.sn-tooltip-basic'));
        const span = spans.find(s => s.textContent.trim() === labelText);
        if (!span) return 'LABEL_NOT_FOUND';
        
        const container = span.closest('.sc_variable_editor');
        if (!container) return 'CONTAINER_NOT_FOUND';
        
        const select = container.querySelector('select');
        if (!select) return 'SELECT_NOT_FOUND';
        
        // Set value
        select.value = 'no';
        
        // Fire ServiceNow-required events
        select.dispatchEvent(new Event('focus', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('blur', { bubbles: true }));
        
        return 'SET_TO_NO';
        }
        """, label)
 
        # ---------------------------
        # SAVE THE RECORD (TOP SAVE)
        # ---------------------------

        # --- Reliable mouse-save (sync Playwright) ---

        save_btn = frame.locator("#sysverb_insert_and_stay")                 # top Save
        save_btn.wait_for(state="visible", timeout=60000)        
        # try real mouse click (hover -> click at center)
        save_btn.hover()
        box = save_btn.bounding_box()
        if box: 
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
        else:
            save_btn.click(force=True)   # fallback if bounding_box None        
        # wait for the ServiceNow success banner
        try:
            frame.locator("div.outputmsg_text").wait_for(state="visible", timeout=60000)
        except:
            # retry mouse click once more (some race conditions)
            save_btn.hover()
            box = save_btn.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)        
            # last-resort: trigger same internal function the button calls
            frame.evaluate("gsftSubmit(document.querySelector('#sysverb_insert_and_stay'))")        
            # final wait for message
            frame.locator("div.outputmsg_text").wait_for(state="visible", timeout=60000)      
    
        # ---------------------------
        # WAIT FOR SAVE RELOAD
        # ---------------------------

        page.wait_for_load_state("domcontentloaded")
        frame = page.frame(name="gsft_main") 
        # Wait for number field

        frame.wait_for_selector('#sys_readonly\\.sc_req_item\\.number', timeout=90000)
        ritm_number = frame.locator('#sys_readonly\\.sc_req_item\\.number').input_value()

        # ----------------    
        # Attachment check
        # ----------------

        # Attachment label
        attach_label = frame.locator("#header_attachment_list_label")
        
        # Attachment count span inside the label
        attach_count_span = attach_label.locator("span[id^='attachmentNumber_']")
        
        try:
            text = attach_count_span.inner_text().strip()
            count = int(text) if text.isdigit() else 0
        except:
            count = 0


        # if attach_count_span.count() > 0:
        #     count = int(attach_count_span.inner_text().strip())
        # else:
        #     count = 0
        
        have_attachment = "Yes" if count > 0 else "No"              
        print(f"{ritm_number} | Saved | Attachment Exists: {have_attachment} | Attachment_count: {count}")
    
        # ---------------------------
        # CLICK BACK BUTTON
        # ---------------------------

       # --- Reliable mouse-back ---
        back_btn = frame.locator("button[onclick*='back.gsftSubmit'], button[aria-label='Back']")
        back_btn.wait_for(state="visible", timeout=60000)
        back_btn.hover()
        box = back_btn.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
        else:
            back_btn.click(force=True)
        
        # wait for list page
        page.wait_for_selector("iframe#gsft_main", timeout=90000)
        frame = page.frame(name="gsft_main")
        frame = page.frame_locator("#gsft_main")
 
        try:
            # Try to find RITM list (short timeout)
            frame.locator("a.linked.formlink").first.wait_for(timeout=8000)            
        
        except:
            # If list not found → dashboard reached
            print("All RITMs processed successfully.")
            print("Returned to dashboard. No more RITMs to process.")
            break
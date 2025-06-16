from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserSession, Controller
import kernel
from kernel import Kernel
from typing import TypedDict, Literal
from pydantic import BaseModel

# QA set-up
# Browser Use is pretty slow—I'd recommend running this in batches of 10 websites at a time.
merchant_websites = [
    "https://jomalone.com/", # Should be "SUCCESS"
    "https://shop.lululemon.com/", # Should be "SUCCESS"
    "https://www.urbanoutfitters.com/", # Should be "SUCCESS"
    "https://www.levi.com/US/en_US/", # Should be "FAILED" - Levi's doesn't have the Afterpay messaging widget
]

prompt = """
Context:
- You are a QA agent.
- You are QA'ing the website for Afterpay.
- You are not sure whether the product is available for Afterpay.
- It's totally okay if you can't find the presence of the text below or logo - it's not a failure. It's possible that the website does not pass our QA.
RETURN ONLY THE WORDS "SUCCESS", "FAILED", OR "UNCERTAIN" - NO OTHER TEXT.

Instructions:
1. Go to the website listed above.

2. Look for a product to click on. If no product is visible on initial load, scroll down slowly until a product appears.

3. If no product is found after scrolling the full page, open the top navigation menu, select a product category (e.g. “Shop” or similar), and wait for the category page to load. Then click on any product.

4. IF CLICKING ON THE PRODUCT IMAGE DOESN'T LOAD THE PRODUCT DETAIL PAGE, TRY CLICKING ON THE PRODUCT NAME. SCROLL DOWN A LITTLE BIT TO MAKE SURE THE PRODUCT NAME IS VISIBLE.

5. After successfully clicking the product, wait for the product detail page to fully load. FROM THIS POINT ON, DO NOT CLICK ON ANY OTHER LINKS OR BUTTONS. THE REST OF THE TASK ONLY OCCURS ON THIS PAGE.

6. Locate a button that says something like "Add to Cart" or "Add to Bag". THIS BUTTON IS CRITICAL FOR YOUR TASK. SCROLL DOWN A LITTLE BIT IF YOU CAN'T IMMEDITELY SEE THE BUTTON. IF YOU CAN'T FIND THIS BUTTON, RETURN "UNCERTAIN".

7. To perform the QA, check directly below it for the text:
- “4 payments of $XX with” (where $XX is any dollar amount).
- See if it has an image after the text. The image should be a dollar sign icon ($), followed by the word "Afterpay".
If both criteria are met, return "SUCCESS". If one or neither is not met, return "FAILED". If you aren't sure, just return "UNCERTAIN".

ONLY LOOK AT THE TEXT UNDERNEATH THE ADD TO CART BUTTON.
"""

# Browser Use set-up
llm = ChatOpenAI(model="gpt-4o")
class AgentOutput(BaseModel):
	result: Literal["SUCCESS", "FAILED", "UNCERTAIN"]
controller = Controller(output_model=AgentOutput)
###

# Kernel set-up
client = Kernel()
app = kernel.App("afterpay")
###


# LLM API Keys are set in the environment during `kernel deploy <filename> -e OPENAI_API_KEY=XXX`
# See https://docs.onkernel.com/launch/deploy#environment-variables

# HOW TO RUN:
# export KERNEL_API_KEY=XXX
# kernel deploy main.py -e OPENAI_API_KEY=XXX
# kernel invoke afterpay start-qa
# (Or via API request: https://docs.onkernel.com/launch/invoke#invoking-via-api%2Fsdk)
# Separate terminal to watch logs: 
# kernel logs afterpay --follow
@app.action("start-qa")
async def start_qa(ctx: kernel.KernelContext):
    kernel_browser = client.browsers.create(invocation_id=ctx.invocation_id, stealth=True)
    print("Kernel browser live view url: ", kernel_browser.browser_live_view_url)
    results = []

    for merchant_website in merchant_websites:
        print(f"Running agent for {merchant_website}")
        result = await run_agent(kernel_browser.cdp_ws_url, merchant_website)
        appended_result = { "website": merchant_website, **result }
        results.append(appended_result)
    # Kernel's return value limit is 64kb, so push this data to S3 or a database if invoking this on long runs
    return results


async def run_agent(cdp_ws_url: str, merchant_website: str):
    agent = Agent(
        #task="Compare the price of gpt-4o and DeepSeek-V3",
        task=f"Merchant website to QA: {merchant_website}" + prompt,
        llm=llm,
        browser_session=BrowserSession(cdp_url=cdp_ws_url,
        controller=controller,
        max_steps=20) # Agent should take 20 steps max
    )
    history = await agent.run()
    agent_output = history.final_result()
    if agent_output:
        print("Returning agent_output")
        print(agent_output)
        return { "result": agent_output }
    else:
        print("Returning errors")
        print(history.errors())
        return { "errors": history.errors() }
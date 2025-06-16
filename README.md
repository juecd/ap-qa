# Kernel Example - Merchant Website QA using Browser Use

This is a simple Kernel application that implements the Browser Use SDK to QA merchant websites for Afterpay.

# HOW TO RUN:
```
export KERNEL_API_KEY=XXX
kernel deploy main.py -e OPENAI_API_KEY=XXX
kernel invoke afterpay start-qa
# (Or via API request: https://docs.onkernel.com/launch/invoke#invoking-via-api%2Fsdk)
# Separate terminal to watch logs:
export KERNEL_API_KEY=XXX
kernel logs afterpay --follow
```

See the [docs](https://docs.onkernel.com/build/browser-frameworks).

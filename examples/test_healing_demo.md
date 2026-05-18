# 🧪 Test Summary: healing_demo

**📅 Date:** 2026-05-18 15:49:18
**🤖 Model:** deepseek/deepseek-chat
**🌐 URL:** [https://the-internet.herokuapp.com/login](https://the-internet.herokuapp.com/login)
**📝 Task:** Open Enter "tomsmith" into the "user_login" field and "SuperSecretPassword!" into the password field
**✅ Status:** FIXED BY AI
**📊 Report:** [reports/report_2026-05-18_15-49-18.html](reports/report_2026-05-18_15-49-18.html)

## 🛠 Self-Healing Details

**🧠 Diagnosis:**

```
# DIAGNOSIS

The test failed because:
1. The original selector `#palyanytsya` doesn't exist in the HTML context (typo/missing element)
2. The actual username field has ID `#username`
3. The password field has ID `#password`
4. The login button is correctly identified by `button[type='submit']`
5. The flash message container is `#flash-messages` (correct)

Found similar interactive elements:
1. Username field: `#username` (correct replacement)
2. Password field: `#password` (correct replacement)
3. Alternative selectors could be:
   - `input[name='username']`
   - `input[type='text']`

Here's the fixed code:
```

**📄 Changed File:** `generated_tests/test_healing_demo.py`
**🔧 Fix applied:** Self-healed existing test. Old snippet: import asyncio
from playwright.async_api import async_playwright

async def test_login():
async ...

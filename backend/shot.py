import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        # 메인 페이지 스크린샷
        await page.goto("http://localhost:8000/", wait_until="networkidle")
        await page.screenshot(path=r"C:\Users\leedh\OneDrive\바탕 화면\workspace\project\ui_main.png", full_page=False)
        print("메인 스크린샷 저장")
        
        # 사무직 선택
        await page.click('button[data-series="사무직"]')
        await asyncio.sleep(0.3)
        
        # 자격증 입력 (첫 행에 컴퓨터활용능력 1급 선택)
        await page.select_option('.cert-name-select', '컴퓨터활용능력')
        await asyncio.sleep(0.2)
        await page.select_option('.cert-grade-select', '1급')
        
        # 자격증 추가 버튼
        await page.click('#btn-add-cert')
        await asyncio.sleep(0.2)
        
        # 두 번째 행에 한국사 선택
        rows = await page.query_selector_all('.cert-name-select')
        await rows[1].select_option('한국사능력검정시험')
        await asyncio.sleep(0.2)
        grades = await page.query_selector_all('.cert-grade-select')
        await grades[1].select_option('1급')
        
        # 토익 점수 입력
        await page.fill('#toeic', '850')
        
        # OPIc 선택
        await page.select_option('#opic', 'IH')
        
        # 입력 완료 스크린샷
        await page.screenshot(path=r"C:\Users\leedh\OneDrive\바탕 화면\workspace\project\ui_input.png", full_page=False)
        print("입력 스크린샷 저장")
        
        # 계산 버튼 클릭
        await page.click('#btn-calculate')
        await page.wait_for_selector('#result-section', state='visible', timeout=10000)
        await asyncio.sleep(1)
        
        # 결과 스크린샷
        await page.screenshot(path=r"C:\Users\leedh\OneDrive\바탕 화면\workspace\project\ui_result.png", full_page=True)
        print("결과 스크린샷 저장")
        
        await browser.close()

asyncio.run(main())

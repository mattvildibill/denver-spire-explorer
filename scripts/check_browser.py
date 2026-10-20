"""Optional real-browser UI checks; requires Python Playwright and Chromium.

Run a local server for dist/ first. GPU timing is deliberately not benchmarked.
"""

import argparse
import asyncio
import fcntl
import json
from pathlib import Path

from playwright.async_api import async_playwright, expect


async def check_maps(playwright, options, output):
    browser = await playwright.chromium.launch(
        executable_path=options.chromium,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-webgl"],
    )
    results = []
    for width, height, touch in [
        (1440, 900, False),
        (390, 844, True),
        (320, 568, True),
        (844, 390, True),
        (1024, 768, True),
    ]:
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            is_mobile=touch,
            has_touch=touch,
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = await page.goto(options.base_url + "/?view=map")
        assert response.status == 200
        await expect(page.locator("#fallback-list li")).to_have_count(6)
        await expect(page.locator("#retry-3d")).to_have_text("Open 3D explorer")
        assert not await page.locator("#fallback").evaluate(
            "element => element.scrollWidth > innerWidth"
        )
        await page.get_by_role("button", name="Larimer Square", exact=True).click()
        await expect(
            page.get_by_role("button", name="Larimer Square", exact=True)
        ).to_have_attribute("aria-pressed", "true")
        await page.locator(".overview-sources summary").click()
        await expect(
            page.get_by_role("link", name="City and County of Denver building outlines")
        ).to_be_visible()
        resources = await page.evaluate(
            "performance.getEntriesByType('resource').map(item => "
            "({name:item.name,bytes:item.decodedBodySize}))"
        )
        runtime = [item for item in resources if "viewer-" in item["name"]]
        assert runtime and all("viewer-map-" in item["name"] for item in runtime)
        assert not any("optimized-" in item["name"] for item in resources)
        assert not errors, errors
        results.append(
            {"viewport": [width, height], "map_runtime_bytes": sum(r["bytes"] for r in runtime)}
        )
        await page.locator("#fallback").evaluate("element => element.scrollTop = 0")
        await page.screenshot(path=str(output / f"map-{width}x{height}.png"))
        await page.close()
    await browser.close()
    return results


async def check_scenes(playwright, options, output):
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    if options.software_rendering:
        args += ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
    browser = await playwright.chromium.launch(executable_path=options.chromium, args=args)
    results = []
    for width, height in [(320, 568), (390, 844), (760, 900), (1280, 800)]:
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            is_mobile=width <= 760,
            has_touch=width <= 760,
            reduced_motion="reduce",
        )
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(options.base_url + "/?quality=low")
        await page.locator("#welcome[open]").wait_for(timeout=30000)
        await page.locator("#free-start").click()
        await page.wait_for_function("document.querySelector('#loading').classList.contains('hidden')")
        if width <= 760:
            rect = await page.locator("#places").bounding_box()
            assert 44 <= rect["height"] <= 70, rect
            assert await page.evaluate(
                "!document.elementFromPoint(innerWidth/2,innerHeight/2).closest('#places')"
            ), "Landmark strip intercepts the center of the scene"
        await expect(page.locator("#tour")).to_be_visible()
        for _ in range(2):
            await page.locator("#tour").click()
            await expect(page.locator("#tour-card")).to_be_visible()
            await page.locator("#tour-next").click()
            await page.locator("#tour-pause").click()
            await expect(page.locator("#tour-pause")).to_have_text("Resume")
            await page.locator("#tour-exit").click()
            await expect(page.locator("#tour-card")).not_to_be_visible()
        await page.locator("#help").click()
        await expect(page.get_by_role("dialog", name="Explore downtown Denver.")).to_be_visible()
        await page.locator("#help-tour").click()
        await expect(page.locator("#tour-card")).to_be_visible()
        await page.locator("#tour-exit").click()
        await page.locator("#overview").click()
        await page.evaluate("new Promise(requestAnimationFrame)")
        assert "1370 m AGL" in await page.locator("#telemetry").inner_text()
        if width == 1280:
            await page.locator("#layers-button").click()
            await expect(page.get_by_role("dialog", name="Layers & light")).to_be_visible()
            await page.locator("#building-search").fill("Spire")
            await page.locator("#find-building").click()
            await expect(page.locator("#building-name")).to_have_text("Spire")
            await page.locator("#share").click()
            await expect(page.get_by_role("dialog", name="Take the city with you.")).to_be_visible()
            await page.locator("#share-dialog .close").click()
            await page.locator("#places .place").first.click()
            await page.locator("#scene-toggle").click()
            await page.screenshot(path=str(output / "portfolio-preview.jpg"), type="jpeg", quality=85)
        else:
            await page.screenshot(path=str(output / f"scene-{width}x{height}.png"))
        assert not errors, errors
        results.append({"viewport": [width, height], "page_errors": errors})
        await context.close()
    await browser.close()
    return results


async def main(options):
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        report = {"maps": await check_maps(playwright, options, output)}
        if not options.maps_only:
            with open(options.webgl_lock, "w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                report["scenes"] = await check_scenes(playwright, options, output)
        (output / "browser-results.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5175")
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--output", default="/tmp/denver-browser-check")
    parser.add_argument("--webgl-lock", default="/tmp/denver-webgl.lock")
    parser.add_argument("--software-rendering", action="store_true")
    parser.add_argument("--maps-only", action="store_true")
    asyncio.run(main(parser.parse_args()))

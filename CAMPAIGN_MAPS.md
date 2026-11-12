# A1–A10 離線地圖與購買提醒

## 使用

1. `npm ci` 安裝既有依賴。
2. `python3 scripts/fetch_maps.py --delay 1` 更新地圖與 `data/acts_data.json`。Python 只用標準函式庫。
3. `npm run electron:dev` 啟動桌面工具；設定中選擇 **PoE1 開荒**。
4. 使用原本的上一章／下一章控制，於「地圖與跑圖指南」手動選取區域。懸停縮圖預覽，點擊放大；滾輪縮放、拖曳平移、Ctrl+滾輪切圖、Esc 關閉。
5. Windows 免安裝版的購買清單位於執行檔旁的 `data/my_gems.json`；開發版則位於 `app.getPath('userData')/my_gems.json`。從「自訂 my_gems.json → 開啟配置資料夾」開啟，編輯後點「重新載入寶石清單」。不覆寫既有檔案。
6. 瀏覽器預覽以匯入 JSON 及 localStorage 取代桌面檔案存取。

## 資料

- `data/acts_data.json`：第一階段 schema 的 `schema_version/game/game_version/route_id/sources/zones/steps`；區域含 `act/zone_name/map_images/speedrun_tips/gem_purchases`。
- `data/my_gems.json`：獨立覆蓋購買清單，按 `zone_id` 對應。空清單或全部 `enabled:false` 時完全隱藏購買區塊。
- `data/route_steps.json`：從原版 DEFAULT_GUIDE 分離的 149 個繁中步驟，保留回城、任務物品、傳送點與首領順序。每一步有固定 ID；原介面的既有自訂攻略與勾選儲存格式仍相容。
- `data/extra_zones.json`：十章城鎮，用於購物提醒；城鎮沒有來源佈局圖片時不虛構圖片。
- `data/route_sources.json`：版本與來源說明。Tytykiller 的購物規劃與競速目標區分原則採自 GGG 官方訪談。Havoc 的 3.23 SRS 文字筆記提供回城配置、圖書館分支與補經驗摘要；影片僅列為參考，沒有冒稱已逐步核實影片內容。
- `assets/maps/act01/` 至 `act10/`：下載原圖。圖片屬來源作者；頁面未提供明確再散布授權，公開發佈前需自行確認授權。
- `data/fetch-report.json`：頁數、圖片數、各章統計與失敗清單。

爬蟲不由主程式、Vite 或 Electron 啟動。每次網路請求至少間隔 1–2 秒（可設定），有逾時、重試、robots.txt 檢查、HTML 快取及圖片續傳。失敗時不覆蓋上次成功的 acts_data.json。來源未提供圖片的頁面會保留空陣列。`.map-cache/` 可刪除以重新抓取頁面文字；原圖依 URL hash 保留。JSON 先完整驗證再原子替換。

原始攻略的版本相關獎勵與任務選擇需依當季核對；不把 2020／2021／3.23 示範標為當季全職業最優路線。地圖是隨機區域的參考佈局，區域選取是手動操作。

## 建置與測試

- `npm run build`：Vite 產生 `build/` 並複製離線圖片，不會抓取網站。
- `npm run electron:windows`：使用 Electron Builder 產生 Windows x64 免安裝資料夾，包含外部 `data/my_gems.json`。
- 根目錄的 `portable-mode.txt` 會停用免安裝版自動更新。
- `npm run test:campaign`：十章資料、圖片存在性、步驟引用、寶石驗證與空清單測試。
- `python3 -m unittest discover -s tests -p 'test_*.py'`：來源文章解析，排除導覽列與頁尾。
- `python3 tests/ui_smoke.py`：Vite 已啟動時測試十章、圖片、放大縮放、寶石狀態與 300/400/800px 版面。需 Python Playwright 與 Chromium；可設定 `CHROMIUM_PATH`。

## 行為檢查範圍

原始碼基準：97f0d9f。現有進度來自手動章節切換、勾選與全域熱鍵；基準沒有 Client.txt 讀取／監聽，也沒有 setIgnoreMouseEvents 滑鼠穿透功能。本次沒有新增、移除或替換這兩項不存在的功能。

檢查 `src/`、`electron/` 及直接依賴，未發現讀取／寫入遊戲行程記憶體，或對遊戲發送模擬按鍵的 API。globalShortcut 僅接收使用者熱鍵，IPC 只更新工具 UI。此為本專案原始碼範圍的檢查，並非對整台電腦、所有二進位檔或遊戲服務條款的絕對保證。

保留原有視窗置頂、透明度、全域熱鍵與自訂攻略。Linux 無畫面 Electron 可測載入、IPC 與渲染；Windows 遊戲前景中的熱鍵／置頂仍需實機驗收。

## 本次驗收結果

- 來源頁面 148、區域 158（含額外十章城鎮）、圖片 537；失敗 0。
- A1–A10 圖片數：92、63、85、53、21、57、46、56、40、24。
- 149 個繁中步驟已獨立存放，未清除使用者既有攻略或進度。
- `npm run test:campaign`：4 個測試通過；Python 文章解析測試通過。
- Chromium：十章切換、地圖載入、懸停、指定圖放大、滾輪縮放、Esc 關閉、空清單隱藏、寶石勾選保存與 300/400/800px 無橫向溢出，全部通過。
- 實際 Electron（Linux、無畫面）：外部 my_gems.json 讀取、重新載入、錯誤 JSON 保留舊清單、快捷鍵設定 API、透明度 API，通過。
- `npm run build` 成功；537 張圖片已複製到 build，檔案大小逐一一致。建置有既有 Browserslist 資料過舊提示及主 JS 大於 500kB 的提示，沒有建置錯誤。
- Electron 直接載入 build/index.html 的 file:// 測試：十章圖片與既有 PoE1/PoE2 切換通過。
- Windows 遊戲前景中的實體全域熱鍵／置頂尚未實測；沒有產製 Windows 安裝程式。

## 修改清單

修改：`.gitignore`、`electron/main.cjs`、`electron/preload.cjs`、`package.json`、`src/App.jsx`、`src/CheatsheetViewer.jsx`、`src/index.css`、`vite.config.js`。

新增：`scripts/fetch_maps.py`、`src/components/CampaignPanel.jsx`、`src/lib/campaign.js`、`data/acts_data.json`、`data/my_gems.json`、`data/extra_zones.json`、`data/route_steps.json`、`data/route_sources.json`、`data/fetch-report.json`、`tests/campaign.test.js`、`tests/test_fetch_maps.py`、`tests/ui_smoke.py`、本文件，以及 `assets/maps/act01/` 至 `act10/` 內的 537 個圖片檔。所有圖片完整檔名列於 `acts_data.json` 各區域的 `map_images[].src`。

`build/` 是生成的正式版輸出；`node_modules/`、`.map-cache/` 是本機依賴與下載快取，不是原始碼修改。

## Windows 免安裝版

從 GitHub Releases 下載 `PoE-Helper-Windows.zip`，完整解壓縮後雙擊 `PoE-Helper-Pro.exe`。不需要 Node.js 或 CMD；不要單獨搬走 EXE。

已生成 Windows x64 PE 執行檔；封裝內 537 張圖片的 SHA-256 逐張比對一致，外部寶石 JSON 與 ZIP 完整性檢查通過。此版本未簽章，Windows 遊戲前景尚未實測。

發布 ZIP 的 SHA-256：`e7c3d9947c89b247c76f2c5cad5cd80031dadc322be571c60e75d43b363617c7`。

`release/` 排除於 Git；EXE 與 ZIP 作為 Release 附件發布。

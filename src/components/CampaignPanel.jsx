import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import campaign from '../../data/acts_data.json';
import defaults from '../../data/my_gems.json';
import { validateGems, purchasesForZone } from '../lib/campaign';
import { CheatsheetViewer } from '../CheatsheetViewer';

const knownZones = new Set(campaign.zones.map(z => z.zone_id));
export default function CampaignPanel({ act }) {
    const zones = campaign.zones.filter(z => z.act === act);
    const [selection, setSelection] = useState('');
    const zone = zones.find(z => z.zone_id === selection) || zones.find(z => z.zone_id.endsWith('-overview')) || zones[0];
    const [gems, setGems] = useState(defaults);
    const [error, setError] = useState('');
    const [configPath, setConfigPath] = useState('');
    const [viewer, setViewer] = useState(null);
    const [hover, setHover] = useState(null);
    const [done, setDone] = useState(() => { try { return JSON.parse(localStorage.getItem('poe_gem_done_v1') || '{}'); } catch { return {}; } });
    const input = useRef(null);
    const reload = async () => {
        try {
            if (window.electronAPI?.loadGemConfig) {
                const result = await window.electronAPI.loadGemConfig();
                if (result.error) throw new Error(result.error);
                setGems(validateGems(JSON.parse(result.content), knownZones)); setConfigPath(result.path);
            } else {
                setGems(validateGems(JSON.parse(localStorage.getItem('poe_custom_gems_v1') || JSON.stringify(defaults)), knownZones));
            }
            setError('');
        } catch (e) { setError(`配置未套用，保留原清單：${e.message}`); }
    };
    useEffect(() => { reload(); }, []);
    useEffect(() => { setViewer(null); setHover(null); }, [act, zone?.zone_id]);
    useEffect(() => {
        if (!viewer) return;
        const key = e => { if (e.key === 'Escape') setViewer(null); };
        window.addEventListener('keydown', key); return () => window.removeEventListener('keydown', key);
    }, [viewer]);
    if (!zone) return null;
    const purchases = purchasesForZone(gems, zone.zone_id);
    const importFile = async e => {
        const file = e.target.files?.[0]; if (!file) return;
        try { if (file.size > 1024 * 1024) throw new Error('JSON 超過 1 MB'); const parsed = validateGems(JSON.parse(await file.text()), knownZones); localStorage.setItem('poe_custom_gems_v1', JSON.stringify(parsed)); setGems(parsed); setError(''); }
        catch (ex) { setError(`匯入失敗：${ex.message}`); }
        e.target.value = '';
    };
    return <section className="campaign-panel" aria-label={`Act ${act} 地圖與提示`}>
        <div className="campaign-heading"><strong>A{act} 地圖與跑圖指南</strong><span>手動選區</span></div>
        <label className="campaign-label">區域<select aria-label="選擇區域" value={zone.zone_id} onChange={e => setSelection(e.target.value)}>
            {zones.map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_name} · {z.map_images.length} 圖</option>)}
        </select></label>
        <p className="campaign-muted">隨機佈局參考 · 懸停預覽／點擊縮放</p>
        {zone.map_images.length ? <div className="campaign-gallery">{zone.map_images.map((im, i) => <button key={im.id} aria-label={`放大 ${im.caption}`} onClick={() => { setHover(null); setViewer(i); }} onMouseEnter={() => setHover(im)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(im)} onBlur={() => setHover(null)}>
            <img loading="lazy" src={`./${im.src}`} alt={im.caption} onError={e => { e.currentTarget.alt = '圖片缺失，請重新執行下載腳本'; }} /><span>{im.caption}</span>
        </button>)}</div> : <p className="campaign-muted">此頁沒有佈局圖，可選擇其他區域。</p>}
        {hover && createPortal(<div className="campaign-hover" aria-hidden="true"><img src={`./${hover.src}`} alt="" /></div>, document.body)}
        {viewer !== null && createPortal(<div className="campaign-lightbox" role="dialog" aria-modal="true" aria-label="區域地圖放大"><CheatsheetViewer key={`${zone.zone_id}-${viewer}`} images={zone.map_images.map(im => `./${im.src}`)} initialIndex={viewer} onClose={() => setViewer(null)} hotkeyLabel="Esc" /></div>, document.body)}
        <details open><summary>Speedrun／區域判讀提示</summary><p className="campaign-muted">區域判讀來自 Definitiv Guide；城鎮提示另附 Tytykiller／Havoc 的具名來源摘要。</p>
            <ul>{zone.speedrun_tips.map((tip,i) => <li key={i}>{tip}</li>)}</ul>
        </details>
        {purchases.length > 0 && <div className="campaign-gems" data-testid="gem-purchases"><strong>購買寶石提醒</strong>{purchases.map(g => {
            const key = `${zone.zone_id}:${g.id}`;
            return <label key={g.id}><input type="checkbox" checked={!!done[key]} onChange={() => { const next = {...done,[key]:!done[key]}; setDone(next); localStorage.setItem('poe_gem_done_v1',JSON.stringify(next)); }} /><span><b>{g.npc} → {g.gem_name} ×{g.quantity}</b>{g.note && <small>{g.note}</small>}{g.conditions?.classes?.length > 0 && <small>職業：{g.conditions.classes.join('、')}</small>}{g.conditions?.quest_completed?.length > 0 && <small>前置任務：{g.conditions.quest_completed.join('、')}</small>}</span></label>;
        })}</div>}
        <details><summary>路線來源與適用範圍</summary><p className="campaign-muted">下方繁中任務清單沿用既有攻略，含回城、任務物品、傳送點與首領順序。獎勵及版本相關內容需依當季核對。</p>{campaign.sources.filter(s => s.id).map(s => <div key={s.id}><a href={s.url} target="_blank" rel="noreferrer">{s.name}</a><p className="campaign-muted">{s.note}</p></div>)}</details>
        <details><summary>自訂 my_gems.json</summary><p className="campaign-muted">本區 ID：{zone.zone_id}</p>{configPath && <p className="campaign-muted">配置檔：{configPath}</p>}
            <div className="campaign-actions"><button onClick={reload}>重新載入寶石清單</button>{window.electronAPI?.openGemConfigFolder ? <button onClick={() => window.electronAPI.openGemConfigFolder()}>開啟配置資料夾</button> : <button onClick={() => input.current?.click()}>匯入 JSON</button>}</div>
            <input ref={input} type="file" accept=".json,application/json" hidden onChange={importFile} />
        </details>
        {error && <p role="alert" className="campaign-error">{error}</p>}
        <a href={zone.source_url} target="_blank" rel="noreferrer">來源：Definitiv Guide · {zone.zone_name}</a>
    </section>;
}

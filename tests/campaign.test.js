import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { validateGems, purchasesForZone, actNumber } from '../src/lib/campaign.js';
const data = JSON.parse(fs.readFileSync(new URL('../data/acts_data.json', import.meta.url)));
const gems = JSON.parse(fs.readFileSync(new URL('../data/my_gems.json', import.meta.url)));
const zones = new Set(data.zones.map(z => z.zone_id));
test('A1–A10 have local maps, tips, stable IDs and detailed route steps', () => {
    assert.equal(zones.size, data.zones.length);
    for (let act = 1; act <= 10; act++) {
        const current = data.zones.filter(z => z.act === act);
        assert.ok(current.some(z => z.map_images.length));
        assert.ok(data.steps.filter(s => s.act === act).length >= 5);
        for (const zone of current) {
            assert.ok(Array.isArray(zone.speedrun_tips));
            assert.ok(Array.isArray(zone.gem_purchases));
            for (const im of zone.map_images) assert.ok(fs.statSync(new URL(`../${im.src}`, import.meta.url)).size > 0);
        }
    }
    for (const step of data.steps) assert.ok(zones.has(step.zone_id), step.zone_id);
});
test('valid custom gems, empty regions and disabled purchases', () => {
    assert.equal(validateGems(gems, zones), gems);
    assert.equal(purchasesForZone(gems, 'a1-coast').length, 0);
    assert.equal(purchasesForZone(gems, 'a6-lioneyes-watch').length, 1);
    const disabled = structuredClone(gems); disabled.zones[0].gem_purchases[0].enabled = false;
    assert.equal(purchasesForZone(disabled, 'a6-lioneyes-watch').length, 0);
});
test('reject unknown zones, duplicates, malformed names and quantities', () => {
    for (const mutate of [x => x.zones[0].zone_id = 'missing', x => x.zones.push(x.zones[0]), x => x.zones[0].gem_purchases[0].quantity = -1, x => x.zones[0].gem_purchases[0].npc = {}, x => x.zones[0].gem_purchases[0].enabled = 'false']) {
        const invalid = structuredClone(gems); mutate(invalid); assert.throws(() => validateGems(invalid, zones));
    }
});
test('chapter selection handles Chinese and rejects unrelated guide names', () => {
    assert.equal(actNumber('第一章'), 1); assert.equal(actNumber('第十章'), 10);
    assert.equal(actNumber('Act 6'), 6); assert.equal(actNumber('我的自訂路線'), null);
});

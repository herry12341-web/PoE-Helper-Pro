export function validateGems(data, zoneIds) {
    if (data?.schema_version !== 1 || !Array.isArray(data.zones)) throw new Error('需要 schema_version: 1 與 zones 陣列');
    const ids = new Set();
    for (const [i, zone] of data.zones.entries()) {
        if (!zoneIds.has(zone.zone_id)) throw new Error(`zones[${i}].zone_id 不存在：${zone.zone_id}`);
        if (ids.has(zone.zone_id)) throw new Error(`重複區域：${zone.zone_id}`);
        ids.add(zone.zone_id);
        if (!Array.isArray(zone.gem_purchases)) throw new Error(`${zone.zone_id}: gem_purchases 必須是陣列`);
        const purchases = new Set();
        for (const gem of zone.gem_purchases) {
            if (typeof gem.id !== 'string' || !gem.id.trim() || purchases.has(gem.id)) throw new Error(`${zone.zone_id}: 購買 id 缺少或重複`);
            purchases.add(gem.id);
            if (typeof gem.npc !== 'string' || !gem.npc.trim() || typeof gem.gem_name !== 'string' || !gem.gem_name.trim()) throw new Error(`${gem.id}: 需要 NPC 與寶石名稱`);
            if (!Number.isInteger(gem.quantity) || gem.quantity < 1) throw new Error(`${gem.id}: quantity 必須是正整數`);
            if (gem.enabled !== undefined && typeof gem.enabled !== 'boolean') throw new Error(`${gem.id}: enabled 必須是布林值`);
            if (gem.conditions !== undefined) {
                if (!gem.conditions || typeof gem.conditions !== 'object' || Array.isArray(gem.conditions)) throw new Error(`${gem.id}: conditions 必須是物件`);
                for (const field of ['classes', 'quest_completed']) {
                    if (gem.conditions[field] !== undefined && (!Array.isArray(gem.conditions[field]) || gem.conditions[field].some(v => typeof v !== 'string'))) throw new Error(`${gem.id}: conditions.${field} 必須是文字陣列`);
                }
            }
            if (gem.note !== undefined && typeof gem.note !== 'string') throw new Error(`${gem.id}: note 必須是文字`);
        }
    }
    return data;
}
export function purchasesForZone(data, zoneId) {
    return (data.zones.find(z => z.zone_id === zoneId)?.gem_purchases || []).filter(g => g.enabled !== false);
}
export function actNumber(title) {
    const chinese = ['第一章','第二章','第三章','第四章','第五章','第六章','第七章','第八章','第九章','第十章'];
    const index = chinese.findIndex(s => title?.startsWith(s));
    if (index >= 0) return index + 1;
    const match = title?.match(/(?:act|章節)\s*(10|[1-9])\b/i);
    return match ? Number(match[1]) : null;
}

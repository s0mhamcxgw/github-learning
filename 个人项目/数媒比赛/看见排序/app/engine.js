(function (root, factory) {
  'use strict';
  const engine = factory(root);
  root.SortLabEngine = engine;
  if (typeof module === 'object' && module.exports) module.exports = engine;
})(typeof globalThis !== 'undefined' ? globalThis : window, function (root) {
  'use strict';
  const TOPICS = Object.freeze(['sports', 'music', 'tech', 'art', 'life', 'nature']);
  const VERSION = '1.0.0';
  const MODEL_VERSION = 'weighted-topic-v1';
  const SCHEMA_VERSION = 1;
  const MAX_EVENTS = 10000;
  const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

  function ensure(condition, message) {
    if (!condition) throw new TypeError(message);
  }

  function initialCounts() {
    return Object.fromEntries(TOPICS.map(topic => [topic, 1]));
  }

  function readCounts(counts) {
    ensure(counts && typeof counts === 'object' && !Array.isArray(counts), '兴趣计数必须是六主题对象。');
    ensure(Object.keys(counts).length === TOPICS.length && TOPICS.every(topic => has(counts, topic)), '兴趣计数必须恰好包含六个已知主题。');
    const result = {};
    let total = 0;
    TOPICS.forEach(topic => {
      ensure(Number.isSafeInteger(counts[topic]) && counts[topic] >= 1, '每个兴趣计数必须是大于等于 1 的安全整数。');
      result[topic] = counts[topic];
      total += counts[topic];
    });
    ensure(Number.isSafeInteger(total), '兴趣计数总和超过安全整数范围。');
    return result;
  }

  function readLambda(lambda) {
    ensure(typeof lambda === 'number' && Number.isFinite(lambda) && lambda >= 0 && lambda <= 1, '兴趣权重 λ 必须是 0 到 1 之间的有限数。');
    return lambda;
  }

  function defaultCards() {
    ensure(root.SortLabData && Array.isArray(root.SortLabData.cards), '模拟内容未加载，请先加载 data.js。');
    return root.SortLabData.cards;
  }

  function copyCard(card) {
    const copy = { id: card.id, topic: card.topic, p: card.p, f: card.f };
    if (has(card, 'title')) copy.title = card.title;
    if (has(card, 'summary')) copy.summary = card.summary;
    return copy;
  }

  function readCards(cards) {
    ensure(Array.isArray(cards) && cards.length > 0, '内容池必须是非空数组。');
    const ids = new Set();
    return cards.map(card => {
      ensure(card && typeof card === 'object' && !Array.isArray(card), '每张内容卡必须是对象。');
      ensure(typeof card.id === 'string' && /^[a-z0-9][a-z0-9-]{0,63}$/.test(card.id), '内容 ID 只能包含小写字母、数字和连字符，长度最多 64。');
      ensure(!ids.has(card.id), '内容池不能包含重复 ID。');
      ids.add(card.id);
      ensure(TOPICS.includes(card.topic), '内容卡包含未知主题。');
      ['p', 'f'].forEach(key => ensure(typeof card[key] === 'number' && Number.isFinite(card[key]) && card[key] >= 0 && card[key] <= 1, '模拟热度和新鲜度必须是 0 到 1 之间的有限数。'));
      ['title', 'summary'].forEach(key => ensure(!has(card, key) || typeof card[key] === 'string', '内容标题和简介必须是文字。'));
      return copyCard(card);
    });
  }

  function compute(counts, lambda = 0.6, cards = defaultCards()) {
    const safeCounts = readCounts(counts);
    readLambda(lambda);
    const safeCards = readCards(cards);
    const total = TOPICS.reduce((sum, topic) => sum + safeCounts[topic], 0);
    const ranked = safeCards.map(card => {
      const interest = safeCounts[card.topic] / total;
      const interestPart = lambda * interest;
      const otherPart = (1 - lambda) * (card.p + card.f) / 2;
      return { ...card, card: copyCard(card), interest, interestPart, otherPart, score: interestPart + otherPart };
    });
    ranked.sort((a, b) => b.score - a.score || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
    return ranked.map((row, index) => ({ ...row, rank: index + 1 }));
  }

  function readEvent(event, cards) {
    ensure(event && typeof event === 'object' && !Array.isArray(event), '点击事件必须是对象。');
    ensure(typeof event.cardId === 'string' && TOPICS.includes(event.topic), '点击事件必须包含有效的 cardId 和 topic。');
    const card = cards.find(item => item.id === event.cardId);
    ensure(card, '点击事件指向不存在的内容卡。');
    ensure(card.topic === event.topic, '点击主题与内容卡主题不一致。');
    return { cardId: event.cardId, topic: event.topic };
  }

  function applySafeEvent(counts, event) {
    const next = { ...counts, [event.topic]: counts[event.topic] + 2 };
    return readCounts(next);
  }

  function applyEvent(counts, event, cards = defaultCards()) {
    const safeCounts = readCounts(counts);
    const safeCards = readCards(cards);
    return applySafeEvent(safeCounts, readEvent(event, safeCards));
  }

  function metrics(ranked, k = 6) {
    ensure(Array.isArray(ranked), '排名必须是数组。');
    ensure(Number.isSafeInteger(k) && k >= 1, '显示长度 K 必须是正整数。');
    ensure(ranked.length >= k, '内容池数量少于显示长度 K，不能静默改变指标分母。');
    const ids = new Set();
    ranked.forEach(row => {
      ensure(row && typeof row.id === 'string' && TOPICS.includes(row.topic), '排名包含无效内容或主题。');
      ensure(!ids.has(row.id), '排名不能包含重复内容 ID。');
      ids.add(row.id);
    });
    const topicCounts = Object.fromEntries(TOPICS.map(topic => [topic, 0]));
    ranked.slice(0, k).forEach(row => { topicCounts[row.topic] += 1; });
    const topicCount = TOPICS.filter(topic => topicCounts[topic] > 0).length;
    return {
      k, topicCount, topicCounts,
      coverage: topicCount / TOPICS.length,
      maxShare: Math.max(...TOPICS.map(topic => topicCounts[topic])) / k,
      coverageDenominator: TOPICS.length,
      shareDenominator: k
    };
  }

  function replay(events, options = {}) {
    ensure(options && typeof options === 'object' && !Array.isArray(options), '回放选项必须是对象。');
    ensure(Array.isArray(events) && events.length <= MAX_EVENTS, '动作序列必须是数组，最多 10000 条。');
    const cards = readCards(options.cards === undefined ? defaultCards() : options.cards);
    ensure(cards.length >= 6, '实验回放至少需要 6 张内容卡。');
    const start = readCounts(options.initialCounts === undefined ? initialCounts() : options.initialCounts);
    const lambda = readLambda(options.lambda === undefined ? 0.6 : options.lambda);
    const safeEvents = events.map(event => readEvent(event, cards));
    const counts = safeEvents.reduce(applySafeEvent, { ...start });
    const ranked = compute(counts, lambda, cards);
    return { initialCounts: start, counts, events: safeEvents, lambda, ranked, metrics: metrics(ranked) };
  }

  function dataVersion() {
    return root.SortLabData && typeof root.SortLabData.version === 'string' ? root.SortLabData.version : VERSION;
  }

  function signature(cards) {
    // Canonical exact content data. This is a consistency marker, not an authenticity signature.
    return JSON.stringify(readCards(cards).sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  }

  function snapshotScores(ranked) {
    return ranked.map(row => ({ id: row.id, topic: row.topic, interest: row.interest, interestPart: row.interestPart, otherPart: row.otherPart, score: row.score, rank: row.rank }));
  }

  function makeSnapshot(options = {}) {
    ensure(options && typeof options === 'object' && !Array.isArray(options), '快照选项必须是对象。');
    const cards = options.cards === undefined ? defaultCards() : options.cards;
    const state = replay(options.events === undefined ? [] : options.events, { ...options, cards });
    return {
      schemaVersion: SCHEMA_VERSION, modelVersion: MODEL_VERSION, dataVersion: dataVersion(),
      dataSignature: signature(cards),
      initialCounts: state.initialCounts, counts: state.counts, events: state.events, lambda: state.lambda,
      order: state.ranked.map(row => row.id), scores: snapshotScores(state.ranked)
    };
  }

  function validateSnapshot(snapshot, cards = defaultCards()) {
    ensure(snapshot && typeof snapshot === 'object' && !Array.isArray(snapshot), '快照必须是对象。');
    ensure(snapshot.schemaVersion === SCHEMA_VERSION, '不支持此快照格式版本。');
    ensure(snapshot.modelVersion === MODEL_VERSION, '快照的模型版本与当前作品不同。');
    ensure(snapshot.dataVersion === dataVersion(), '快照的数据版本与当前作品不同。');
    ensure(snapshot.dataSignature === signature(cards), '快照内容池与当前版本不同。');
    ensure(has(snapshot, 'initialCounts') && has(snapshot, 'events') && has(snapshot, 'lambda'), '快照缺少初始计数、动作或参数。');
    const fresh = makeSnapshot({ initialCounts: snapshot.initialCounts, events: snapshot.events, lambda: snapshot.lambda, cards });
    const storedCounts = readCounts(snapshot.counts);
    ensure(TOPICS.every(topic => storedCounts[topic] === fresh.counts[topic]), '快照计数与动作回放结果不一致。');
    ensure(Array.isArray(snapshot.order) && snapshot.order.length === fresh.order.length && snapshot.order.every((id, index) => id === fresh.order[index]), '快照排名与动作回放结果不一致。');
    ensure(Array.isArray(snapshot.scores) && snapshot.scores.length === fresh.scores.length && snapshot.scores.every((row, index) => row && Object.keys(fresh.scores[index]).every(key => row[key] === fresh.scores[index][key])), '快照分数与动作回放结果不一致。');
    return fresh;
  }

  function restoreSnapshot(snapshot, options = {}) {
    ensure(options && typeof options === 'object' && !Array.isArray(options), '恢复选项必须是对象。');
    const cards = options.cards === undefined ? defaultCards() : options.cards;
    const safe = validateSnapshot(snapshot, cards);
    return replay(safe.events, { initialCounts: safe.initialCounts, lambda: options.lambda === undefined ? safe.lambda : options.lambda, cards });
  }

  return Object.freeze({
    version: VERSION, modelVersion: MODEL_VERSION, schemaVersion: SCHEMA_VERSION, topics: TOPICS,
    initialCounts, compute, applyEvent, replay, metrics, makeSnapshot, createSnapshot: makeSnapshot,
    validateSnapshot, restoreSnapshot
  });
});

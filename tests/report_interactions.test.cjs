// Run with Node 18+: node --test tests/report_interactions.test.cjs
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');

const html = readFileSync(
  join(__dirname, '../src/asago_policy_mapper/templates/risk_extraction_report.jinja2'),
  'utf8',
);
const script = html.match(/<script>\s*(function reportApp\(\)[\s\S]*?)<\/script>/)[1];
const createApp = new Function('DATA', script + '\nreturn reportApp();');

function fixture() {
  return { risks: [
    { risk_id: 'a', risk_name: 'Clear retrieval', taxonomy: 'ibm-risk-atlas', grounding_confidence: 'high', accepted_by: 'rrf', confidence: 0.02 },
    { risk_id: 'b', risk_name: 'Judge candidate', taxonomy: 'mit-ai-risk-repository', grounding_confidence: 'medium', accepted_by: 'llm_judge', confidence: 0.95 },
    { risk_id: 'c', risk_name: 'Weak expansion', taxonomy: 'ibm-risk-atlas', grounding_confidence: 'low', accepted_by: 'expansion', confidence: 0 },
    { risk_id: 'd', risk_name: 'Skipped grounding', taxonomy: 'customer-taxonomy', grounding_confidence: 'ungrounded', accepted_by: 'auto_promoted', confidence: 0.8 },
    { risk_id: 'e', risk_name: 'Older result', accepted_by: 'threshold', confidence: 0.4 },
    { risk_id: 'f', risk_name: 'Clear expansion', taxonomy: 'mit-ai-risk-repository', grounding_confidence: 'high', accepted_by: 'expansion', confidence: 0 },
  ] };
}

const ids = risks => risks.map(risk => risk.risk_id);

test('chart selections toggle taxonomy filters while summary counts stay unchanged', () => {
  const input = fixture();
  const original = JSON.stringify(input);
  const app = createApp(input);
  const counts = () => [app.riskCount, app.taxonomyCount, app.highCount, app.reviewCount];
  assert.deepEqual(counts(), [6, 3, 2, 3]);
  assert.equal(app.taxonomyDistribution.reduce((sum, item) => sum + item.count, 0), 6);
  assert.equal(app.groundingDistribution.reduce((sum, item) => sum + item.count, 0), 6);
  const distributions = JSON.stringify([app.taxonomyDistribution, app.groundingDistribution]);

  app.toggleChartFilter('filterTaxonomy', 'ibm-risk-atlas');
  assert.deepEqual(ids(app.visibleRisks), ['a', 'c']);
  app.toggleChartFilter('filterTaxonomy', 'mit-ai-risk-repository');
  assert.deepEqual(ids(app.visibleRisks), ['a', 'b', 'c', 'f']);
  app.toggleChartFilter('filterTaxonomy', 'ibm-risk-atlas');
  assert.deepEqual(ids(app.visibleRisks), ['b', 'f']);
  assert.deepEqual(counts(), [6, 3, 2, 3]);
  assert.equal(JSON.stringify([app.taxonomyDistribution, app.groundingDistribution]), distributions);
  assert.equal(JSON.stringify(input), original);
});

test('multi-select filters combine alternatives within a filter and intersect between filters', () => {
  const app = createApp(fixture());
  app.filterAcceptedBy = ['rrf', 'llm_judge'];
  app.filterGrounding = ['high', 'medium'];
  app.filterTaxonomy = ['ibm-risk-atlas', 'mit-ai-risk-repository'];
  assert.deepEqual(ids(app.visibleRisks), ['a', 'b']);
  app.searchQuery = ' JUDGE ';
  assert.deepEqual(ids(app.visibleRisks), ['b']);
  app.toggleChartFilter('filterGrounding', 'medium');
  assert.equal(app.visibleRisks.length, 0);
  assert.equal(app.hasActiveFilters, true);
  app.resetFilters();
  assert.equal(app.visibleRisks.length, 6);
  assert.equal(app.hasActiveFilters, false);
});

test('review shortcut clears previous filters and reveals all suggested reviews', () => {
  const app = createApp(fixture());
  app.filterTaxonomy = ['ibm-risk-atlas'];
  app.filterAcceptedBy = ['rrf'];
  app.searchQuery = 'no results';
  let scrolled = false;
  app.scrollToFindings = () => { scrolled = true; };
  app.showReviewMatches();
  assert.deepEqual(ids(app.visibleRisks), ['b', 'c', 'd']);
  assert.equal(app.visibleRisks.length, app.reviewCount);
  assert.equal(app.sortBy, 'grounding_confidence');
  assert.equal(app.sortDesc, false);
  assert.equal(scrolled, true);
});

test('grounding sort uses support levels independently of retrieval scores', () => {
  const input = fixture();
  const app = createApp(input);
  const sorted = () => ids(app.sortedRisks(app.visibleRisks, app.sortBy, app.sortDesc));
  assert.deepEqual(sorted(), ['f', 'a', 'b', 'c', 'd', 'e']);
  assert.deepEqual(ids(input.risks), ['a', 'b', 'c', 'd', 'e', 'f']);
  app.toggleSort('grounding_confidence');
  assert.deepEqual(sorted(), ['e', 'd', 'c', 'b', 'f', 'a']);
});

test('missing taxonomy and grounding remain visible and filterable', () => {
  const app = createApp(fixture());
  const missing = app.taxonomyDistribution.find(item => app.taxonomyLabel(item.value) === 'No taxonomy');
  assert.equal(missing.count, 1);
  assert.equal(app.groundingDistribution.find(item => item.value === 'unknown').count, 1);
  assert.ok(app.taxonomyOptions(app.data.risks).includes('customer-taxonomy'));
  app.toggleChartFilter('filterTaxonomy', missing.value);
  app.toggleChartFilter('filterGrounding', 'unknown');
  assert.deepEqual(ids(app.visibleRisks), ['e']);
});

test('empty reports have finite chart values and sensible missing metadata', () => {
  const app = createApp({});
  assert.deepEqual([app.riskCount, app.taxonomyCount, app.highCount, app.reviewCount], [0, 0, 0, 0]);
  assert.deepEqual(app.visibleRisks, []);
  assert.deepEqual(app.taxonomyDistribution, []);
  assert.equal(app.taxonomyMax, 1);
  assert.equal(app.matchShare(0), '0%');
  assert.match(app.summaryText, /No risk matches/);
  assert.equal(app.formatPercent(undefined), '—');
  assert.equal(app.formatPercent(0), '0%');
  assert.equal(app.formatDate(undefined), '');
  assert.deepEqual(app.themeDistribution, []);
  assert.match(app.themeCoverageText, /0 of 0/);
});

function themeFixture() {
  const data = fixture();
  data.theme_catalog = [
    { id: 'privacy', label: 'Privacy & confidentiality' },
    { id: 'security', label: 'Security & resilience' },
  ];
  data.risks[0].theme_ids = ['privacy', 'security'];
  data.risks[1].theme_ids = ['privacy'];
  data.risks[2].theme_ids = ['security'];
  data.risks[3].theme_ids = ['other'];
  data.risks[5].theme_ids = ['privacy', 'privacy'];
  return data;
}

test('themes count overlapping memberships once and combine selections without duplicate findings', () => {
  const input = themeFixture();
  const original = JSON.stringify(input);
  const app = createApp(input);
  assert.deepEqual(app.themeDistribution.map(t => [t.id, t.count]), [['privacy', 3], ['security', 2], ['other', 2]]);
  assert.match(app.themeCoverageText, /4 of 6/);
  assert.equal(app.themeDistribution[0].taxonomyCount, 2);
  const distribution = JSON.stringify(app.themeDistribution);
  app.toggleChartFilter('filterThemes', 'privacy');
  assert.equal(app.themeFilterLabel, 'Privacy & confidentiality');
  assert.deepEqual(ids(app.visibleRisks), ['a', 'b', 'f']);
  app.toggleChartFilter('filterThemes', 'security');
  assert.equal(app.themeFilterLabel, '2 selected');
  assert.deepEqual(ids(app.visibleRisks), ['a', 'b', 'c', 'f']);
  app.filterTaxonomy = ['ibm-risk-atlas'];
  app.filterGrounding = ['high'];
  app.filterAcceptedBy = ['rrf'];
  assert.deepEqual(ids(app.visibleRisks), ['a']);
  app.searchQuery = 'nothing';
  assert.deepEqual(ids(app.visibleRisks), []);
  assert.equal(JSON.stringify(app.themeDistribution), distribution);
  assert.equal(JSON.stringify(input), original);
});

test('ungrouped and missing themes remain selectable; reset and review clear theme selections', () => {
  const app = createApp(themeFixture());
  app.filterThemes = ['other'];
  assert.deepEqual(ids(app.visibleRisks), ['d', 'e']);
  assert.equal(app.hasActiveFilters, true);
  app.resetFilters();
  assert.deepEqual(app.filterThemes, []);
  assert.equal(app.visibleRisks.length, 6);
  assert.equal(app.themeFilterLabel, 'All');
  assert.equal(app.hasActiveFilters, false);
  app.filterThemes = ['privacy'];
  app.scrollToFindings = () => {};
  app.showReviewMatches();
  assert.deepEqual(app.filterThemes, []);
  assert.deepEqual(ids(app.visibleRisks), ['b', 'c', 'd']);
  const older = createApp(fixture());
  assert.deepEqual(older.themeDistribution.map(t => [t.id, t.count]), [['other', 6]]);
});

function explainScores(metadata, scores, acceptedBy = 'threshold') {
  const app = createApp({ metadata });
  return Object.fromEntries(app.scoreBreakdown({ scores, accepted_by: acceptedBy }).map(score => [score.key, score]));
}

test('disabled reranking is explained as unused while other measured scores remain visible', () => {
  const rows = explainScores({ use_cross_encoder: false, cross_encoder_model: null }, {
    bm25_rank: 1, embedding_distance: 0.315471, cross_encoder_score: 0, rrf_score: 0.03252247,
  });
  assert.equal(rows.bm25_rank.value, '1');
  assert.equal(rows.embedding_distance.value, '0.3155');
  assert.equal(rows.cross_encoder_score.value, 'Not run');
  assert.match(rows.cross_encoder_score.interpretation, /placeholder/);
  assert.equal(rows.rrf_score.value, '0.0325');
});

test('known measured zero and tiny reranker scores are preserved', () => {
  const settings = { use_cross_encoder: true, query_gen: false, cross_encoder_model: 'reranker' };
  assert.equal(explainScores(settings, { cross_encoder_score: 0 }).cross_encoder_score.value, '0.0000');
  assert.equal(explainScores(settings, { cross_encoder_score: 0.0000001 }).cross_encoder_score.value, '1.00e-7');
  assert.equal(explainScores(settings, { cross_encoder_score: 0.83 }).cross_encoder_score.value, '0.8300');
});

test('expansion placeholders do not look like best ranks or failed relevance scores', () => {
  const rows = explainScores({}, {
    bm25_rank: 0, embedding_distance: 0, cross_encoder_score: 0, rrf_score: 0,
  }, 'expansion');
  assert.ok(Object.values(rows).every(row => row.value === 'Not used'));
  assert.ok(Object.values(rows).every(row => /related risks/.test(row.interpretation)));
});

test('missing keyword ranks and ambiguous semantic zeros are explained separately', () => {
  const rows = explainScores({}, { bm25_rank: 0, embedding_distance: 0, cross_encoder_score: 0, rrf_score: 0 });
  assert.equal(rows.bm25_rank.value, 'Not ranked');
  assert.equal(rows.embedding_distance.value, '0.0000');
  assert.match(rows.embedding_distance.interpretation, /unrecorded default/);
  assert.equal(rows.cross_encoder_score.value, '0.0000');
  assert.match(rows.cross_encoder_score.interpretation, /may be a placeholder/);
  assert.equal(rows.rrf_score.value, 'Not recorded');
});

test('query fallback and keyword rescue do not falsely classify zero as a skipped step', () => {
  for (const settings of [
    { use_cross_encoder: true, query_gen: true },
    { use_cross_encoder: true, query_gen: false, bm25_rescue_rank: 5 },
  ]) {
    const row = explainScores(settings, { cross_encoder_score: 0, bm25_rank: 1 }).cross_encoder_score;
    assert.equal(row.value, '0.0000');
    assert.match(row.interpretation, /placeholder or a scored result/);
  }
});

test('ColBERT similarity is retained even when the cross-encoder is disabled', () => {
  const settings = { colbert_model: 'colbert', use_cross_encoder: false, cross_encoder_model: null };
  const rows = explainScores(settings, { embedding_distance: 0, cross_encoder_score: 0.72 });
  assert.match(rows.cross_encoder_score.label, /ColBERT/);
  assert.equal(rows.cross_encoder_score.value, '0.7200');
  assert.equal(rows.embedding_distance.value, 'Not used');
  assert.equal(explainScores(settings, { cross_encoder_score: 0 }).cross_encoder_score.value, 'Not ranked');
});

test('absent and invalid scores stay distinct from zero placeholders', () => {
  for (const scores of [undefined, {}, { bm25_rank: null, embedding_distance: NaN, cross_encoder_score: Infinity }]) {
    assert.ok(Object.values(explainScores({}, scores)).every(row => row.value === 'Not recorded'));
  }
});
